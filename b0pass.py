from datetime import datetime
import os
from pathlib import Path
import shutil
import zipfile
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from tqdm import tqdm
from loguru import logger

# 设置服务器地址IP和端口
SERVER_IP = "127.0.0.1"
SERVER_PORT = "8888"
# 要上传的文件路径
UPLOAD_DIR = Path("D:/文件定时上传目录")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# 每日上传时间
UPLOAD_TIME = "15:00"
# 日志文件
logger.add(
    "百灵快传定时上传日志.log", rotation="100 MB", retention="7 days", compression="zip"
)


def compress_folder_to_zip(folder_path, zip_path):
    """
    压缩文件夹
    """
    # 获取文件列表
    file_list = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_list.append(os.path.join(root, file))

    # 使用 tqdm 显示进度
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in tqdm(file_list, desc="压缩文件夹", unit="file"):
            # 保留相对路径
            arcname = os.path.relpath(file, folder_path)
            zipf.write(file, arcname=arcname)


def upload_file(file_path: Path):
    """
    上传文件到百灵快传服务器

    FILE_PATH = "E:/大学搜题酱folder_50.zip"
    参数:
    file_path: 要上传的文件路径
    """
    # 构建完整的上传URL, 使用 https://github.com/bitepeng/b0pass 的文件上传接口
    upload_url = f"http://{SERVER_IP}:{SERVER_PORT}/pass/file-upload"

    # 准备文件
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/octet-stream")}
        # 发送POST请求
        response = requests.post(upload_url, files=files)
        if response.status_code != 200:
            raise Exception(f"文件上传失败: {response.status_code} -- {response.text}")
        return response.json()


def upload_file_task():
    """
    上传文件任务
    """
    logger.info("定时任务开始执行上传文件...")
    # 遍历上传目录下的所有文件, 随后删除
    for file_path in UPLOAD_DIR.iterdir():
        try:
            if file_path.is_file():
                up_load_path = file_path
            elif file_path.is_dir():
                up_load_path = file_path.with_suffix(".zip")
                compress_folder_to_zip(file_path, up_load_path)
                # PermissionError
                # file_path.unlink()  # 压缩后删除原文件夹
                shutil.rmtree(file_path)
            else:
                logger.warning(f"非法文件类型不上传: {file_path}")
                continue
            json_data = upload_file(up_load_path)
            logger.debug(f"上传返回结果: {json_data}")
        except Exception as e:
            logger.error(f"{up_load_path} 文件上传失败: {e}")
        else:
            up_load_path.unlink()  # 上传成功后删除上传的文件
            logger.success(f"文件上传成功: {up_load_path}")
    logger.info("定时任务上传文件结束...")


# 使用示例
if __name__ == "__main__":
    # upload_file_task()   # 测试使用, 直接执行
    scheduler = BlockingScheduler()
    # 立即执行一次
    scheduler.add_job(upload_file_task, "date", run_date=datetime.now())

    # 每天执行, 解析 UPLOAD_TIME 时间
    hour, minute = UPLOAD_TIME.split(":")
    scheduler.add_job(upload_file_task, "cron", hour=hour, minute=minute)
    scheduler.start()
