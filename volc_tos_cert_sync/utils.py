# -*- coding: utf-8 -*-
# Copyright 2026 Your Name
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
工具函数模块 - 企业微信通知、证书处理等
"""
import datetime
import json
import os
from urllib import request
from typing import Tuple
from OpenSSL import crypto
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from .config import Config


def send_wecom_alert(title: str, content: str, level: str = "info") -> None:
    """
    发送企业微信告警
    :param title: 通知标题
    :param content: 通知内容
    :param level: 级别 (info/error)
    """
    if not Config.WECOM_WEBHOOK:
        return

    try:
        # 构建消息体
        if level == "error":
            msg_content = f"# ❌ {title}\n{content}"
        else:
            msg_content = f"✅ {title}\n{content}"

        cert_info = get_cert_validity_info()
        msg_content += cert_info

        data = {
            "msgtype": "text",
            "text": {"content": msg_content}
        }

        # 发送请求
        req = request.Request(
            url=Config.WECOM_WEBHOOK,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        # 设置超时
        with request.urlopen(req, timeout=10) as resp:
            if resp.getcode() != 200:
                print(f"⚠️  企业微信通知发送失败，响应码：{resp.getcode()}")

    except Exception as e:
        print(f"⚠️  企业微信通知发送异常：{str(e)}")


def read_cert_and_calc_fingerprint() -> Tuple[str, str]:
    """
    读取本地证书并计算 SHA256 指纹
    :return: (证书内容, 证书指纹)
    """
    try:
        # 读取证书文件
        with open(Config.CERT_CRT_PATH, "r", encoding="utf-8") as f:
            cert_content = f.read().strip()

        # 清理证书内容
        clean_pem = cert_content.replace("\\n", "\n").strip("`").strip()

        # 加载证书并计算指纹
        cert_obj = crypto.load_certificate(crypto.FILETYPE_PEM, clean_pem)
        fingerprint_bytes = cert_obj.digest("sha256")
        fingerprint = fingerprint_bytes.decode("utf-8").replace(":", "").upper()

        print(f"✅ 本地证书读取成功，SHA256指纹：{fingerprint}")
        return cert_content, fingerprint

    except FileNotFoundError:
        raise Exception(f"证书文件不存在：{Config.CERT_CRT_PATH}")
    except crypto.Error as e:
        raise Exception(f"证书解析失败：{str(e)}")
    except Exception as e:
        raise Exception(f"读取证书失败：{str(e)}")


def read_private_key() -> str:
    """读取本地私钥文件"""
    try:
        with open(Config.CERT_KEY_PATH, "r", encoding="utf-8") as f:
            key_content = f.read().strip()
        return key_content
    except Exception as e:
        raise Exception(f"读取私钥失败：{str(e)}")


def get_cert_validity_info() -> str:
    """
    解析证书有效期，返回格式化的文本信息（适配企业微信text消息）
    :return: 有效期文本，示例：
    "\n📅 证书有效期：
    - 生效时间：2026-03-01 08:00:00
    - 过期时间：2027-03-01 08:00:00
    - 剩余天数：365天
    - 状态：正常"
    """
    # 证书路径从配置中获取
    cert_path = Config.CERT_CRT_PATH

    # 证书文件不存在时返回提示
    if not os.path.exists(cert_path):
        return "\n📅 证书有效期：证书文件不存在"

    try:
        # 读取并解析证书
        with open(cert_path, "rb") as f:
            cert_data = f.read()
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())

        # 转换为UTC+8时区（适配国内时间）
        tz = datetime.timezone(datetime.timedelta(hours=8))
        not_before = cert.not_valid_before_utc.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
        not_after = cert.not_valid_after_utc.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")

        # 计算剩余天数
        now = datetime.datetime.now(tz)
        expire_time = cert.not_valid_after_utc.astimezone(tz)
        days_remaining = (expire_time - now).days
        status = "✅ 正常" if days_remaining >= 0 else "❌ 已过期"

        # 拼接文本信息（适配企业微信text格式，换行用\n）
        validity_info = f"""
📅 证书有效期：
- 生效时间：{not_before}
- 过期时间：{not_after}
- 剩余天数：{days_remaining}天
- 状态：{status}"""

        return validity_info

    except Exception as e:
        return f"\n📅 证书有效期：解析失败 - {str(e)}"
