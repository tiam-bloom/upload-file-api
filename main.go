package main

import (
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"sync"
	"time"
)

const uploadDir = "./uploads"

var (
	mu       sync.Mutex
	progress = make(map[string]int) // 用于记录每个文件已上传的分块数
)

// UploadInfo 用于解析上传请求的 JSON 数据
type UploadInfo struct {
	FileName   string `json:"file_name"`   // 文件名
	FileMD5    string `json:"file_md5"`    // 文件的 MD5 标识
	ChunkIndex int    `json:"chunk_index"` // 当前分块的索引
	ChunkTotal int    `json:"chunk_total"` // 总分块数
}

// CORS 中间件
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// 设置 CORS 响应头
		w.Header().Set("Access-Control-Allow-Origin", "*") // 允许所有来源(允许跨域)
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		w.Header().Set("Access-Control-Allow-Credentials", "true")

		// 对于 OPTIONS 请求，直接返回
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		// 继续处理其他请求
		next.ServeHTTP(w, r)
	})
}

// uploadHandler 处理文件分块上传
func uploadHandler(w http.ResponseWriter, r *http.Request) {
	// fmt.Println("接收到上传请求...", r.Body)
	// 限制请求方法为 POST
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 解析 multipart 表单
	err := r.ParseMultipartForm(10 << 20) // 最大 10MB 内存，超出部分写入临时文件
	if err != nil {
		http.Error(w, "Failed to parse form: "+err.Error(), http.StatusBadRequest)
		return
	}

	// 从表单中读取 JSON 元数据
	jsonData := r.FormValue("json")
	if jsonData == "" {
		http.Error(w, "Missing JSON metadata", http.StatusBadRequest)
		return
	}

	// 解析 JSON 数据
	var info UploadInfo
	if err := json.Unmarshal([]byte(jsonData), &info); err != nil {
		http.Error(w, "Invalid JSON metadata: "+err.Error(), http.StatusBadRequest)
		return
	}
	fmt.Printf("解析的JSON数据: %+v\n", info)
	// 从表单中获取文件块
	file, _, err := r.FormFile("chunk")
	if err != nil {
		http.Error(w, "Failed to get file chunk: "+err.Error(), http.StatusBadRequest)
		return
	}
	defer file.Close()
	// 输出文件块的元数据以便调试
	// fmt.Printf("Received chunk: %s, size: %d bytes\n", header.Filename, header.Size)

	// 创建上传文件的临时目录
	tempDir := filepath.Join(uploadDir, info.FileMD5)
	if err := os.MkdirAll(tempDir, os.ModePerm); err != nil {
		http.Error(w, "Failed to create directory", http.StatusInternalServerError)
		return
	}

	// 保存分块文件
	chunkPath := filepath.Join(tempDir, fmt.Sprintf("%d", info.ChunkIndex))

	// 检查分块是否已存在
	if _, err := os.Stat(chunkPath); err == nil {
		// 更新上传进度
		mu.Lock()
		progress[info.FileMD5]++
		currentProgress := progress[info.FileMD5]
		mu.Unlock()
		// 分块已存在，直接返回成功
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"progress": currentProgress,
		})
		return
	}

	outFile, err := os.Create(chunkPath)
	if err != nil {
		http.Error(w, "Failed to save chunk: "+err.Error(), http.StatusInternalServerError)
		return
	}
	defer outFile.Close()

	if _, err := io.Copy(outFile, file); err != nil {
		http.Error(w, "Failed to write chunk", http.StatusInternalServerError)
		return
	}

	// 更新上传进度
	mu.Lock()
	progress[info.FileMD5]++
	currentProgress := progress[info.FileMD5]
	mu.Unlock()
	// fmt.Printf("当前上传进度: %d, 总分块数: %d\n", currentProgress, info.ChunkTotal)

	// 检查是否完成所有分块上传
	if currentProgress == info.ChunkTotal {
		// 合并分块
		finalPath := filepath.Join(uploadDir, info.FileName)
		if err := mergeChunks(tempDir, finalPath, info.ChunkTotal); err != nil {
			http.Error(w, "Failed to merge chunks: "+err.Error(), http.StatusInternalServerError)
			return
		}
		fmt.Println("分块合并完成")

		// 校验 MD5
		calculatedMD5, err := calculateMD5(finalPath)
		if err != nil {
			http.Error(w, "Failed to calculate MD5: "+err.Error(), http.StatusInternalServerError)
			return
		}

		if calculatedMD5 != info.FileMD5 {
			http.Error(w, "MD5 mismatch", http.StatusInternalServerError)
			return
		}
		fmt.Println("MD5校验通过")

		// 清理临时分块 TODO 最后一个分块无法被清理, 待修复
		//  https://github.com/golang/go/issues/51442
		// https://github.com/golang/go/issues/52986
		time.Sleep(500 * time.Millisecond) // 确保文件句柄已释放
		if err := os.RemoveAll(tempDir); err != nil {
			fmt.Printf("Failed to remove temporary files: %v\n", err)
		}
		fmt.Println("临时分块清理完成")
		// 上传完成
		mu.Lock()
		delete(progress, info.FileMD5)
		mu.Unlock()

		// 返回成功响应
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"progress": currentProgress,
			"status":   "completed",
		})
		return
	}

	// 返回上传进度
	w.Header().Set("Content-Type", "application/json")
	// fmt.Println("返回上传进度")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"progress": currentProgress,
	})
}

// mergeChunks 合并所有分块到一个完整文件
func mergeChunks(tempDir, finalPath string, totalChunks int) error {
	finalFile, err := os.Create(finalPath)
	if err != nil {
		return err
	}
	defer finalFile.Close()

	for i := 0; i < totalChunks; i++ {
		chunkPath := filepath.Join(tempDir, strconv.Itoa(i))
		chunkFile, err := os.Open(chunkPath)
		if err != nil {
			return err
		}

		if _, err := io.Copy(finalFile, chunkFile); err != nil {
			chunkFile.Close()
			return err
		}
		chunkFile.Close()
	}
	return nil
}

// calculateMD5 计算文件的 MD5
func calculateMD5(filePath string) (string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	hash := md5.New()
	if _, err := io.Copy(hash, file); err != nil {
		return "", err
	}
	return hex.EncodeToString(hash.Sum(nil)), nil
}

func main() {
	// 创建上传目录
	if err := os.MkdirAll(uploadDir, os.ModePerm); err != nil {
		fmt.Println("Failed to create upload directory:", err)
		return
	}

	// 配置路由
	http.Handle("/upload", corsMiddleware(http.HandlerFunc(uploadHandler)))
	// 添加根路由处理
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/" {
			http.ServeFile(w, r, "index.html")
			return
		}
		http.NotFound(w, r)
	})

	fmt.Println("Server is running on http://localhost:8080")
	http.ListenAndServe(":8080", nil)
}
