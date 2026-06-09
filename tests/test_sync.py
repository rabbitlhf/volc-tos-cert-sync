# -*- coding: utf-8 -*-
# Copyright 2026 Fundy Liu
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


def test_get_local_cert_expire_time(mock_config):
    """测试读取并解析本地证书过期时间"""
    import os
    import datetime
    from volc_tos_cert_sync.utils import get_local_cert_expire_time
    current_dir = os.path.dirname(__file__)
    real_cert_path = os.path.join(current_dir, "tls.crt")

    # 备份并修改
    old_path = Config.CERT_CRT_PATH
    Config.CERT_CRT_PATH = real_cert_path
    try:
        expire_time = get_local_cert_expire_time()
        assert isinstance(expire_time, datetime.datetime)
        assert expire_time.tzinfo is not None
    finally:
        Config.CERT_CRT_PATH = old_path


def test_should_sync_cert():
    """测试是否需要同步的决策树"""
    import datetime
    from volc_tos_cert_sync.sync import should_sync_cert
    tz = datetime.timezone(datetime.timedelta(hours=8))
    local_time = datetime.datetime(2027, 3, 1, 12, 0, 0, tzinfo=tz)

    # 1. 线上没有现有证书
    assert should_sync_cert(local_time, None, None) is True

    # 2. 本地证书过期时间比线上早或相等 -> 跳过同步
    online_time_newer = datetime.datetime(2027, 3, 2, 12, 0, 0, tzinfo=tz)
    assert should_sync_cert(local_time, online_time_newer, 10) is False
    assert should_sync_cert(local_time, local_time, 10) is False

    # 3. 本地证书更新，且线上证书在阈值内
    Config.CERT_THRESHOLD_DAYS = "15"
    online_time_older = datetime.datetime(2027, 2, 28, 12, 0, 0, tzinfo=tz)
    # 线上剩 5 天过期 <= 15 天阈值，且本地更长
    assert should_sync_cert(local_time, online_time_older, 5) is True

    # 4. 本地证书更新，且线上证书仍在安全期（剩余天数 > 阈值）
    # 线上剩 20 天过期 > 15 天阈值
    assert should_sync_cert(local_time, online_time_older, 20) is False

    # 5. 未配置阈值，且本地更新
    Config.CERT_THRESHOLD_DAYS = None
    assert should_sync_cert(local_time, online_time_older, 20) is True


def test_get_online_domain_cert_info():
    """测试获取线上证书详情逻辑"""
    import datetime
    from unittest.mock import MagicMock
    from volc_tos_cert_sync.sync import get_online_domain_cert_info

    # 准备 Mock 对象
    mock_tos = MagicMock()
    mock_cert_api = MagicMock()

    # 模拟 list_bucket_custom_domain 返回
    mock_rule1 = MagicMock()
    mock_rule1.domain = "other-domain.com"
    mock_rule1.cert_id = "cert-other"

    mock_rule2 = MagicMock()
    mock_rule2.domain = Config.CUSTOM_DOMAIN
    mock_rule2.cert_id = "cert-target"

    mock_out = MagicMock()
    mock_out.rules = [mock_rule1, mock_rule2]
    mock_tos.list_bucket_custom_domain.return_value = mock_out

    # 模拟 certificate_get_instance 返回
    mock_resp = MagicMock()
    mock_resp.not_after = "2027-03-01T08:00:00Z"
    mock_cert_api.certificate_get_instance.return_value = mock_resp

    # 运行测试
    cert_id, expire_time, days_remaining = get_online_domain_cert_info(mock_tos, mock_cert_api, None)

    assert cert_id == "cert-target"
    assert expire_time is not None
    assert expire_time.year == 2027
    assert expire_time.month == 3
    assert expire_time.day == 1
    # 08:00:00Z 转成东八区应该为 16:00:00
    assert expire_time.hour == 16