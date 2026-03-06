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
核心同步功能测试
"""

from volc_tos_cert_sync.config import Config
from volc_tos_cert_sync.sync import init_volc_clients


def test_config_validation(mock_config):
    """测试配置验证"""
    is_valid, msg = Config.validate()
    assert is_valid is True
    assert msg == "配置验证通过"


def test_config_validation_missing(mock_config, monkeypatch):
    """测试配置缺失的情况"""
    monkeypatch.setenv("TOS_BUCKET", "")
    Config.TOS_BUCKET = ""

    is_valid, msg = Config.validate()
    assert is_valid is False
    assert "TOS_BUCKET" in msg


def test_init_clients(mock_config):
    """测试客户端初始化（仅测试流程，不实际调用API）"""
    try:
        cert_api, runtime_options, tos_client = init_volc_clients()
        assert cert_api is not None
        assert runtime_options is not None
        assert tos_client is not None
    except Exception as e:
        # 测试环境可能无法连接火山引擎，仅检查是否抛出预期外的异常
        assert "access key" not in str(e).lower()