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
核心同步逻辑模块 - 火山引擎证书操作、TOS绑定等
"""

import datetime
from typing import Optional

import volcenginesdkcore
from volcenginesdkcore.configuration import Configuration
from volcenginesdkcore.rest import ApiException
from volcenginesdkcore.interceptor import RuntimeOption
from volcenginesdkcertificateservice.api.certificate_service_api import CERTIFICATESERVICEApi
from volcenginesdkcertificateservice.models.certificate_get_instance_list_request import CertificateGetInstanceListRequest
from volcenginesdkcertificateservice.models.certificate_get_instance_request import CertificateGetInstanceRequest
from volcenginesdkcertificateservice.models.import_certificate_request import ImportCertificateRequest
import tos
from tos.models2 import CustomDomainRule

from .config import Config
from .utils import send_wecom_alert, read_cert_and_calc_fingerprint, read_private_key


def init_volc_clients():
    """初始化火山引擎客户端"""
    # 初始化证书服务配置
    cert_config = Configuration()
    cert_config.access_key = Config.VOLC_ACCESS_KEY
    cert_config.secret_key = Config.VOLC_SECRET_KEY
    cert_config.region = Config.VOLC_REGION
    cert_config.debug = False
    volcenginesdkcore.Configuration.set_default(cert_config)

    # 证书服务客户端
    cert_runtime_options = RuntimeOption(
        ak=cert_config.access_key,
        sk=cert_config.secret_key,
        client_side_validation=True
    )
    cert_api = CERTIFICATESERVICEApi()

    # TOS 客户端
    tos_client = tos.TosClientV2(
        Config.VOLC_ACCESS_KEY,
        Config.VOLC_SECRET_KEY,
        Config.TOS_ENDPOINT,
        Config.VOLC_REGION
    )

    return cert_api, cert_runtime_options, tos_client


def get_matched_cert_id(cert_api, runtime_options, local_fingerprint: str) -> Optional[str]:
    """
    查询火山证书中心中匹配指纹的证书 ID
    :param cert_api: 证书服务 API 实例
    :param runtime_options: 运行时配置
    :param local_fingerprint: 本地证书指纹
    :return: 匹配的证书 ID，无则返回 None
    """
    try:
        # 构建查询请求
        list_request = CertificateGetInstanceListRequest(
            domain=Config.CUSTOM_DOMAIN,
            status=["Issued"],
            project_name=Config.VOLC_PROJECT,
            page_number=1,
            page_size=20,
            _configuration=runtime_options
        )

        # 执行查询
        list_resp = cert_api.certificate_get_instance_list(list_request)
        certificates = list_resp.instances
        print(f"✅ 查询到 {len(certificates)} 个{Config.CUSTOM_DOMAIN}域名下的已签发证书")

        # 遍历匹配指纹
        for cert in certificates:
            # 兼容字典/对象格式
            if isinstance(cert, dict):
                instance_id = cert.get("InstanceId")
            else:
                instance_id = getattr(cert, "instance_id", None)

            if not instance_id:
                continue

            # 查询证书详情
            detail_request = CertificateGetInstanceRequest(
                instance_id=instance_id,
                project_name=Config.VOLC_PROJECT,
                _configuration=runtime_options
            )
            detail_resp = cert_api.certificate_get_instance(detail_request)
            cert_detail = detail_resp.certificate_detail

            # 获取平台指纹
            if hasattr(cert_detail, 'finger_print_sha256'):
                platform_fingerprint = cert_detail.finger_print_sha256.upper()
            elif hasattr(cert_detail, 'fingerprint_sha256'):
                platform_fingerprint = cert_detail.fingerprint_sha256.upper()
            else:
                continue

            print(f"🔍 证书{instance_id}平台指纹：{platform_fingerprint} | 本地指纹：{local_fingerprint}")
            if platform_fingerprint == local_fingerprint:
                print(f"✅ 找到匹配指纹的证书，InstanceId: {instance_id}")
                return instance_id

        print("⚠️  未找到匹配指纹的证书")
        return None

    except ApiException as e:
        raise Exception(f"查询证书列表失败 [火山错误码:{e.status}]：{e.reason}")
    except Exception as e:
        raise Exception(f"查询证书异常：{str(e)}")


def upload_new_cert(cert_api, runtime_options, cert_content: str, key_content: str) -> str:
    """
    上传新证书到火山引擎证书中心
    :param cert_api: 证书服务 API 实例
    :param runtime_options: 运行时配置
    :param cert_content: 证书内容
    :param key_content: 私钥内容
    :return: 新证书的 InstanceId
    """
    try:
        # 构建上传请求
        certificate_info = {
            "CertificateChain": cert_content,
            "PrivateKey": key_content
        }

        upload_request = ImportCertificateRequest(
            repeatable=True,
            no_verify_and_fix_chain=False,
            project_name=Config.VOLC_PROJECT,
            certificate_info=certificate_info,
            _configuration=runtime_options
        )

        # 执行上传
        upload_resp = cert_api.import_certificate(upload_request)
        instance_id = getattr(upload_resp, "instance_id", None)

        if not instance_id:
            raise Exception("上传证书成功，但未获取到 InstanceId")

        print(f"✅ 新证书上传成功，InstanceId: {instance_id}")
        return instance_id

    except ApiException as e:
        raise Exception(f"上传证书失败 [火山错误码:{e.status}]：{e.reason}")
    except Exception as e:
        raise Exception(f"上传证书异常：{str(e)}")


def check_tos_bucket(tos_client) -> bool:
    """检查 TOS Bucket 是否存在且可访问"""
    try:
        head_resp = tos_client.head_bucket(
            bucket=Config.TOS_BUCKET,
            project_name=Config.VOLC_PROJECT
        )
        # 请求参数中的 project_name 貌似没有过滤效果，这里根据结果再次匹配验证一次
        if head_resp.project_name == Config.VOLC_PROJECT:
            return True
        else:
            print(f"❌ 项目 {Config.VOLC_PROJECT} 下 TOS桶 {Config.TOS_BUCKET} 不存在，存在项目 {head_resp.project_name} 下的 TOS桶，请检查配置")
            return False
    except tos.exceptions.TosServerError as e:
        if e.status_code == 404:
            print(f"❌ 项目 {Config.VOLC_PROJECT} 下 TOS桶 {Config.TOS_BUCKET} 不存在（HTTP 404）")
        elif e.status_code == 403:
            print(f"❌ 无权限访问 TOS桶 {Config.TOS_BUCKET}（HTTP 403）")
        else:
            print(f"❌ 检查 TOS桶 失败：HTTP {e.status_code} - {e.message}")
        return False
    except tos.exceptions.TosClientError as e:
        print(f"❌ TOS 客户端错误：{e.message}")
        return False
    except Exception as e:
        print(f"❌ 检查 TOS桶 异常：{str(e)}")
        return False


def update_tos_domain_cert(tos_client, instance_id: str):
    """更新 TOS 自定义域名的证书绑定"""
    if not instance_id:
        raise Exception("证书 InstanceId 为空，无法更新 TOS 域名配置")

    try:
        domain_rule = CustomDomainRule(
            domain=Config.CUSTOM_DOMAIN,
            cert_id=instance_id
        )
        tos_client.put_bucket_custom_domain(Config.TOS_BUCKET, domain_rule)
        print(f"✅ TOS桶 {Config.TOS_BUCKET} 自定义域名 {Config.CUSTOM_DOMAIN} 证书绑定成功（InstanceId: {instance_id}）")

    except tos.exceptions.TosClientError as e:
        raise Exception(f"TOS 客户端错误：message={e.message}, cause={e.cause}")
    except tos.exceptions.TosServerError as e:
        error_info = (
            f"TOS 服务端错误 - Code:{e.code}, RequestId:{e.request_id}, "
            f"Message:{e.message}, HTTP Code:{e.status_code}, EC:{e.ec}"
        )
        raise Exception(error_info)
    except Exception as e:
        raise Exception(f"更新 TOS 域名证书异常：{str(e)}")


def sync_certificate() -> None:
    """
    核心同步逻辑 - 完整的证书同步流程
    """
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_content = (
        f"开始执行 TOS 证书同步\n"
        f"开始时间：{start_time}\n"
        f"域名：{Config.CUSTOM_DOMAIN}\n"
        f"Bucket：{Config.TOS_BUCKET}\n"
        f"区域：{Config.VOLC_REGION}\n"
        f"项目：{Config.VOLC_PROJECT}"
    )
    print(log_content)

    try:
        # 1. 配置验证
        print("\n===== 1. 配置验证 =====")
        is_valid, config_msg = Config.validate()
        if not is_valid:
            raise Exception(config_msg)
        print(f"✅ {config_msg}")

        # 2. 初始化客户端
        print("\n===== 2. 初始化火山引擎客户端 =====")
        cert_api, cert_runtime_options, tos_client = init_volc_clients()
        print("✅ 客户端初始化完成")

        # 3. 检查 TOS Bucket
        print("\n===== 3. 检查 TOS Bucket =====")
        if not check_tos_bucket(tos_client):
            raise Exception("TOS Bucket 校验失败，流程终止")

        # 4. 读取证书和私钥
        print("\n===== 4. 读取证书并计算指纹 =====")
        cert_content, cert_fingerprint = read_cert_and_calc_fingerprint()
        key_content = read_private_key()

        # 5. 查询匹配证书
        print("\n===== 5. 查询火山证书中心 =====")
        matched_cert_id = get_matched_cert_id(cert_api, cert_runtime_options, cert_fingerprint)

        # 6. 上传新证书（如果需要）
        if not matched_cert_id:
            print("\n===== 6. 上传新证书 =====")
            matched_cert_id = upload_new_cert(cert_api, cert_runtime_options, cert_content, key_content)
        else:
            print("\n===== 6. 证书已存在，无需上传 =====")

        # 7. 更新 TOS 域名证书
        print("\n===== 7. 更新 TOS 域名证书绑定 =====")
        update_tos_domain_cert(tos_client, matched_cert_id)

        # 执行成功
        end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_content = (
            f"{log_content}\n"
            f"结束时间：{end_time}\n"
            f"状态：成功\n"
            f"证书指纹：{cert_fingerprint}"
        )
        send_wecom_alert("TOS 证书同步成功", success_content, "info")
        print("\n🎉 TOS 证书同步全流程完成！")

    except Exception as e:
        error_msg = f"流程执行失败：{str(e)}"
        print(f"\n❌ {error_msg}")
        send_wecom_alert("TOS 证书同步失败", f"{error_msg}\n{log_content}", "error")
        raise  # 抛出异常供上层处理