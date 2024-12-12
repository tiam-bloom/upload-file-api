from datetime import datetime
import os
from pathlib import Path
import shutil
import zipfile
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from tqdm import tqdm
from loguru import logger
from tenacity import *

# 设置服务器地址IP和端口
SERVER_IP = "127.0.0.1"
SERVER_PORT = "8888"
# 要上传的文件路径
UPLOAD_DIR = Path("D:/文件定时上传目录")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# 每日上传时间
UPLOAD_TIMES = ["10:00", "15:00", "22:00"]
# todesk 设备号
TODESK_NO = "1234567890"
# 日志文件
logger.add(
    "百灵快传定时上传日志.log", rotation="100 MB", retention="7 days", compression="zip"
)


def compress_file_name(folder_path: Path) -> Path:
    """
    定义压缩文件名规则
    folder_path: 文件夹路径
    return: 压缩文件路径
    """
    # 统计文件数量
    files = [f for f in folder_path.glob("**/*") if f.is_file()]
    file_count = len(files)
    # 统计总文件夹数量(包括子集嵌套的文件夹)
    dirs = [d for d in folder_path.glob("**/*") if d.is_dir()]
    dir_count = len(dirs)
    # 一级文件夹数量(不包括子集嵌套的文件夹)
    folder1_count = len(list(folder_path.iterdir()))
    logger.debug(
        f"一级文件数量: {folder1_count}, 总文件数量: {file_count}, 总文件夹数量: {dir_count}"
    )
    # TODO: 修改单题数量计算规则
    num_count = file_count // 5
    # 修改文件后缀为zip
    zip_path = folder_path.with_suffix(".zip")
    # TODO: 修改定义压缩文件名规则
    # new_name = f"{zip_path.stem}-{TODESK_NO}-{file_count}-{datetime.now().strftime('%Y%m%d-%H%M%S')}{zip_path.suffix}"
    new_name = f"{TODESK_NO}-{zip_path.stem}-{num_count}{zip_path.suffix}"
    logger.debug(f"新规则压缩文件名: {new_name}")
    zip_path = zip_path.with_name(new_name)
    return zip_path


def compress_folder_to_zip(folder_path: Path):
    """
    压缩文件夹
    """
    # 获取文件列表
    file_list = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_list.append(os.path.join(root, file))
    zip_path = compress_file_name(folder_path)
    # 使用 tqdm 显示进度
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in tqdm(file_list, desc=f"压缩文件夹中: {folder_path}", unit="file"):
            # 保留相对路径
            arcname = os.path.relpath(file, folder_path)
            zipf.write(file, arcname=arcname)
    return zip_path


def post_upload_file(file_path: Path):
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
        json_data = response.json()
        if json_data["code"] != 0:
            raise Exception(f"文件上传失败: {json_data['code']} -- {json_data['msg']}")
        return json_data["msg"]


# 上传文件重试, 重试5次, 每次等待间隔3秒
@retry(
    stop=stop_after_attempt(5),
    #    wait=wait_exponential(multiplier=1, min=3, max=10),  # 指数等待3-10秒, 每次等待时间递增
    #    wait=wait_random(min=4, max=10),  # 随机等待3-10秒
    wait=wait_fixed(3),
    before=before_log(logger, logger.level("DEBUG").no),
    after=after_log(logger, logger.level("DEBUG").no),
)
def upload_file(file_path: Path):
    if file_path.is_file():
        up_load_path = file_path
    elif file_path.is_dir():
        up_load_path = compress_folder_to_zip(file_path)
        # 压缩后删除原文件夹
        shutil.rmtree(file_path)
    else:
        logger.warning(f"未知文件类型不上传: {file_path}")
        return
    msg = post_upload_file(up_load_path)
    up_load_path.unlink()  # 上传成功后删除上传的文件
    logger.success(f"文件 {up_load_path} 上传返回结果: {msg}")


def upload_file_task():
    """
    上传文件任务
    """
    logger.info("定时任务开始执行上传文件...")
    # 遍历上传目录下的所有一级文件, 随后删除
    for file_path in UPLOAD_DIR.iterdir():
        try:
            upload_file(file_path)
        except Exception as e:
            logger.error(f"{file_path} 文件上传失败: {e}")
    logger.info("定时任务上传文件结束...")


# 使用示例
if __name__ == "__main__":
    upload_file_task()  # 测试使用, 直接执行
    # scheduler = BlockingScheduler()
    # # 立即执行一次
    # # scheduler.add_job(upload_file_task, "date", run_date=datetime.now())
    # # 每天执行, 解析 UPLOAD_TIME 时间
    # for time in UPLOAD_TIMES:
    #     hour, minute = time.split(":")
    #     scheduler.add_job(upload_file_task, "cron", hour=hour, minute=minute)
    # # 启动调度器
    # scheduler.start()
