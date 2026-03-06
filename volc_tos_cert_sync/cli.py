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
命令行接口模块
"""

import traceback
import argparse

from .sync import sync_certificate
from .__init__ import __version__


def main():
    """
    命令行入口函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="火山引擎TOS证书同步工具",
        prog="volc-tos-cert-sync"
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    # 执行同步流程
    try:
        sync_certificate()
    except Exception as e:
        print(f"\n❌ 同步失败：{str(e)}")
        print(f"\n详细错误信息：\n{traceback.format_exc()}")
        exit(1)


if __name__ == "__main__":
    main()