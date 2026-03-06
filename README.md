# volc-tos-cert-sync

火山引擎TOS证书同步工具 - 自动同步本地SSL证书到火山引擎证书中心，并绑定到TOS自定义域名。

## 功能特点
- 自动读取本地证书文件并计算SHA256指纹
- 查询火山引擎证书中心，避免重复上传
- 自动上传新证书并绑定到TOS自定义域名
- 企业微信消息通知（成功/失败）
- 支持源码/虚拟环境/Docker 三种运行方式

## 安装
```bash
# 从PyPI安装（如果发布）
pip install volc_tos_cert_sync

# 或从源码安装
git clone https://github.com/your-username/volc_tos_cert_sync.git
cd volc_tos_cert_sync
pip install -r requirements.txt
```
## 安装和运行
### 方式1：源码运行（虚拟环境推荐）
```bash
# 克隆项目
git clone https://github.com/your-username/volc_tos_cert_sync.git
cd volc_tos_cert_sync

# 安装运行依赖
# 1. 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

# 环境变量
# 火山引擎密钥（必填）
export VOLC_ACCESS_KEY="your-access-key"
export VOLC_SECRET_KEY="your-secret-key"

# TOS配置（必填）
export TOS_BUCKET="your-bucket-name"
export CUSTOM_DOMAIN="your-domain.com"

# 可选配置
export VOLC_REGION="cn-guangzhou"
export VOLC_PROJECT="Production"
export CERT_CRT_PATH="/etc/cert/tls.crt"
export CERT_KEY_PATH="/etc/cert/tls.key"
export WECOM_WEBHOOK="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"

# 运行工具
# 方式1：直接运行
python -m volc_tos_cert_sync

# 方式2：通过命令行
volc-tos-cert-sync

# 或安装为命令行工具
pip install .
volc-tos-cert-sync
```
### 方式 2：Docker 运行（推荐生产环境）
```bash
# 1. 构建镜像
docker build -t volc-tos-cert-sync:latest .

# 2. 运行容器（挂载证书+配置环境变量）
docker run --rm \
  -v /宿主机证书目录:/etc/cert \  # 替换为你的证书实际路径
  -e VOLC_ACCESS_KEY="你的access-key" \
  -e VOLC_SECRET_KEY="你的secret-key" \
  -e TOS_BUCKET="你的bucket" \
  -e CUSTOM_DOMAIN="你的域名" \
  -e WECOM_WEBHOOK="你的企业微信webhook" \  # 可选
  volc-tos-cert-sync:latest
```

### 方式 3：定时运行（Docker + Crontab）
```bash
# 添加到系统定时任务（每天凌晨2点执行）
0 2 * * * docker run --rm -v /etc/cert:/etc/cert -e VOLC_ACCESS_KEY="xxx" -e VOLC_SECRET_KEY="xxx" -e TOS_BUCKET="xxx" -e CUSTOM_DOMAIN="xxx" volc-tos-cert-sync:latest >> /var/log/volc_tos_sync.log 2>&1
```

## 开发
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/ -v --cov=volc_tos_cert_sync

# 代码格式化
black volc_tos_cert_sync/ tests/
```

## 许可证
Apache-2.0 许可证
