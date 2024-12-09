from datetime import datetime
import hashlib
import json
from pathlib import Path
import zipfile
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import hashlib
import requests
from typing import Dict, Any
from tqdm import tqdm
import shutil
from loguru import logger

logger.add("logs/file_upload.log", rotation="100 MB", compression="zip")

# A scheduler that runs in the foreground
scheduler = BlockingScheduler()


def calculate_file_md5(file_path: str, chunk_size: int = 2 * 1024 * 1024) -> str:
    """计算文件的MD5值"""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def upload(file_path: str) -> Dict[str, Any]:
    """
    上传文件函数
    :param file_path: 文件路径
    :return: 上传结果
    """
    # 定义分块大小（2MB）
    chunk_size = 2 * 1024 * 1024

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 获取文件信息
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)

    logger.info(f"开始上传文件，文件大小: {file_size / 1024 / 1024:.2f} MB")
    logger.info("计算文件MD5...")

    # 计算文件MD5
    file_md5 = calculate_file_md5(file_path)
    total_chunks = (file_size + chunk_size - 1) // chunk_size

    logger.info(f"文件MD5: {file_md5}")
    logger.info(f"总分块数: {total_chunks}")

    # 分块上传
    with open(file_path, "rb") as f:
        # 使用tqdm创建进度条
        with tqdm(total=total_chunks, desc=f"上传文件: {file_name}", unit="块") as pbar:
            for chunk_index in range(total_chunks):
                chunk = f.read(chunk_size)

                # 准备上传数据
                data = {
                    "file_name": file_name,
                    "file_md5": file_md5,
                    "chunk_index": chunk_index,
                    "chunk_total": total_chunks,
                }

                files = {"json": (None, json.dumps(data)), "chunk": (file_name, chunk)}

                try:
                    response = requests.post(
                        "http://localhost:8080/upload",  # 根据实际情况修改服务器地址
                        files=files,
                    )

                    response.raise_for_status()
                    result = response.json()

                    # 更新进度条
                    pbar.update(1)

                    if result.get("status") == "completed":
                        logger.info("\n文件上传完成！")
                        return result

                except requests.exceptions.RequestException as e:
                    raise Exception(f"上传失败: {str(e)}")


def compress_folder_to_zip(folder_path, zip_path):
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


def upload_file_task():
    upload_dir = Path(r"D:\文件定时上传目录")
    if not upload_dir.exists():
        logger.error(f"文件夹不存在: {upload_dir}")
        return
    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            logger.info(f"开始上传文件: {file_path}")
            try:
                upload(file_path)
                file_path.unlink()
            except Exception as e:
                logger.error(f"上传失败: {str(e)}")
        elif file_path.is_dir():
            # 文件夹压缩为zip
            zip_path = file_path.with_suffix(".zip")
            logger.info(f"开始压缩文件夹: {file_path} 为 {zip_path}")
            compress_folder_to_zip(file_path, zip_path)
            # 删除目录
            shutil.rmtree(file_path)
            try:
                upload(zip_path)
                zip_path.unlink()
            except Exception as e:
                logger.error(f"上传失败: {str(e)}")


# 立即执行一次
scheduler.add_job(upload_file_task, "date", run_date=datetime.now())
# 每天 15:00 执行一次
scheduler.add_job(upload_file_task, "cron", hour=15, minute=0)

# 每3秒执行一次
# scheduler.add_job(print_now, "interval", seconds=3)

# 使用 corn 表达式, 周一到周六的每天早上 9 点到下午 18 点之间，每隔 1 分钟执行一次
# sched.add_job(print_now, CronTrigger.from_crontab('*/1 9-17 * * 1-6'))

if __name__ == "__main__":
    print("定时任务 ~ 启动! ")
    scheduler.start()
    # upload_file_task()
    print(
        "定时任务 ~ 结束!"
    )  # 使用 BlockingScheduler 时, 这里将不会被执行, 定时任务会阻塞主线程
