

## 下载go编译器

https://golang.google.cn/dl/


服务端:启动上传服务

```
go run main.go
```

客户端:启动web服务, 修改目标ip为服务端ip

```
npm i anywhere -g
anywhere -p 8080

# 或者使用python内置的http.server
python -m http.server 8080
```




访问 http://localhost:8080/, 通过web界面上传文件

或者运行 python 定时调度.py 文件, 定时上传指定目录下的一级文件(文件夹自动打包为zip), 上传成功会自动删除, 注意备份



## v2版本

使用 https://github.com/bitepeng/b0pass  开源接口作为上传文件接口
b0pass.py 定时上传指定目录中的所有 一级文件, 上传成功后自动删除; 若存在一级文件夹, 则先压缩后(会删除原文件夹)再上传
