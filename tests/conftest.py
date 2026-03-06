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
pytest 全局配置和夹具
"""

import os
import pytest
from volc_tos_cert_sync.config import Config


@pytest.fixture()
def mock_config(monkeypatch):
    """模拟配置 - 用于测试"""
    # 设置环境变量
    monkeypatch.setenv("VOLC_ACCESS_KEY", "test-access-key")
    monkeypatch.setenv("VOLC_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("TOS_BUCKET", "test-bucket")
    monkeypatch.setenv("CUSTOM_DOMAIN", "test-domain.com")

    # 重置Config类的属性
    Config.VOLC_ACCESS_KEY = "test-access-key"
    Config.VOLC_SECRET_KEY = "test-secret-key"
    Config.TOS_BUCKET = "test-bucket"
    Config.CUSTOM_DOMAIN = "test-domain.com"

    # 模拟证书文件
    with open("/tmp/test.crt", "w") as f:
        f.write("fake cert content")
    with open("/tmp/test.key", "w") as f:
        f.write("fake key content")

    monkeypatch.setenv("CERT_CRT_PATH", "/tmp/test.crt")
    monkeypatch.setenv("CERT_KEY_PATH", "/tmp/test.key")
    Config.CERT_CRT_PATH = "/tmp/test.crt"
    Config.CERT_KEY_PATH = "/tmp/test.key"

    yield

    # 清理
    os.remove("/tmp/test.crt")
    os.remove("/tmp/test.key")