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
配置管理模块
"""

import os
from typing import Tuple


class Config:
    """配置类 - 统一管理所有环境变量配置"""

    # 证书文件路径
    CERT_CRT_PATH = os.getenv("CERT_CRT_PATH", "/etc/cert/tls.crt")
    CERT_KEY_PATH = os.getenv("CERT_KEY_PATH", "/etc/cert/tls.key")

    # 火山引擎基础配置
    VOLC_REGION = os.getenv("VOLC_REGION", "cn-guangzhou")
    VOLC_PROJECT = os.getenv("VOLC_PROJECT", "Production")
    TOS_BUCKET = os.getenv("TOS_BUCKET")
    CUSTOM_DOMAIN = os.getenv("CUSTOM_DOMAIN")
    TOS_ENDPOINT = os.getenv("TOS_ENDPOINT", f"tos-{VOLC_REGION}.volces.com")

    # 敏感密钥
    VOLC_ACCESS_KEY = os.getenv("VOLC_ACCESS_KEY")
    VOLC_SECRET_KEY = os.getenv("VOLC_SECRET_KEY")
    WECOM_WEBHOOK = os.getenv("WECOM_WEBHOOK", "")

    @classmethod
    def validate(cls) -> Tuple[bool, str]:
        """验证配置完整性"""
        # 检查必填配置
        missing = []
        for key in ["VOLC_ACCESS_KEY", "VOLC_SECRET_KEY", "TOS_BUCKET", "CUSTOM_DOMAIN"]:
            if not getattr(cls, key):
                missing.append(key)

        if missing:
            return False, f"缺失必选配置：{', '.join(missing)}"

        # 检查证书文件
        if not os.path.exists(cls.CERT_CRT_PATH):
            return False, f"证书文件不存在：{cls.CERT_CRT_PATH}"
        if not os.path.exists(cls.CERT_KEY_PATH):
            return False, f"私钥文件不存在：{cls.CERT_KEY_PATH}"

        return True, "配置验证通过"
