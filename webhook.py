# 文档地址: https://developer.work.weixin.qq.com/document/path/91770
# webhook地址: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=27fa95fa-6c01-4364-8dc3-8424ff54f490
# 限制: 每个机器人发送的消息不能超过20条/分钟。

import requests

# pip install pypinyin
from pypinyin import lazy_pinyin


def send_webhook(content: str, at_users: list[str] = [], at_all: bool = False):
    """
    发送企业微信群机器人webhook消息
    :param content: 消息内容
    :param at_users: 需要@的用户列表
    :param at_all: 是否@所有人
    :return: 返回发送结果
    """
    headers = {
        "Content-Type": "application/json",
    }
    params = {
        "key": "27fa95fa-6c01-4364-8dc3-8424ff54f490",
    }
    # 转换为拼音
    pinyin_users = []
    for user in at_users:
        pinyin_users.append("".join(lazy_pinyin(user)))
    if at_all:
        pinyin_users.append("@all")

    json_data = {
        "msgtype": "text",
        "text": {
            "content": content,
            "mentioned_list": pinyin_users,  # @all 表示所有人
        },
    }
    response = requests.post(
        "https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
        params=params,
        headers=headers,
        json=json_data,
    )
    response.raise_for_status()
    json_data = response.json()
    if json_data["errcode"] != 0:
        raise Exception(f"发送失败: {json_data['errmsg']}")
    return json_data


if __name__ == "__main__":
    send_webhook("你的程序出BUG啦!!! 快来改", at_users=["王晗斌", "冯宇汀", "杨跃彪"])
