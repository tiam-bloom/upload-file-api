from pathlib import Path
import time


UPLOAD_DIR = Path("D:/文件定时上传目录")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def main():
    while True:
        dir_path = Path(UPLOAD_DIR, "测试待上传文件夹")
        dir_path.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time() * 1000)
        filename = f"测试文件_{timestamp}.txt"
        file_path = Path(dir_path, filename)
        print(f"写入文件: {file_path}")
        # 写入一个10MB的文件, 随便内容, 占空间就好了
        size = 10 * 1024 * 1024
        with open(file_path, "wb") as f:
            f.write(b"0" * size)
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("程序已停止")
