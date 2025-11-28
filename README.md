# NAS Tools Chrome 服务器

一个基于 FastAPI 的 Chrome 自动化服务器，为 NAS 工具提供浏览器自动化能力，通过 RESTful API 提供服务。

## 项目结构

```
nas-tools-chrome/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── main.py            # 主 FastAPI 应用
│   ├── config/            # 配置模块
│   │   ├── __init__.py
│   │   └── settings.py    # 应用设置和常量
│   ├── core/              # 核心功能
│   │   ├── __init__.py
│   │   └── browser_manager.py  # 浏览器管理
│   ├── api/               # API 层
│   │   ├── __init__.py
│   │   ├── schemas.py     # 请求/响应模式
│   │   └── routes.py      # API 路由处理器
│   └── utils/             # 工具函数
│       ├── __init__.py
│       └── challenge_utils.py  # 挑战检测工具
├── main.py                # 应用入口点
├── pyproject.toml         # 项目配置和依赖管理
├── Dockerfile            # Docker 配置
├── supervisord.conf      # 进程管理
├── start.sh              # 启动脚本
└── README.md             # 本文件
```

## 功能特性

- **浏览器自动化**: 创建和管理浏览器标签页
- **CloudFlare 挑战处理**: 自动检测和解决 CloudFlare 挑战
- **RESTful API**: 简洁的浏览器操作 API 端点
- **异步支持**: 使用 async/await 构建，性能更佳
- **Docker 支持**: 使用 Docker 轻松部署
- **网页 VNC**: 通过 noVNC 网页界面查看 Chrome 浏览器会话

## API 端点

### 根路径
- `GET /` - API 信息和可用端点

### 标签页管理
- `POST /tabs/` - 创建新的浏览器标签页
- `GET /tabs/` - 列出所有活动标签页
- `GET /tabs/{tab_name}/html` - 从标签页获取 HTML 内容
- `POST /tabs/click/` - 在标签页中点击元素
- `DELETE /tabs/{tab_name}` - 关闭特定标签页

## 安装部署

### 直接安装

1. 克隆仓库：
```bash
git clone https://github.com/linyuan0213/nas-tools-chrome.git
cd nas-tools-chrome
```

2. 使用 uv 安装依赖：
```bash
uv sync
```

3. 运行服务器：
```bash
uvicorn main:app --host 0.0.0.0 --port 9850
```

### Docker 部署

1. 构建镜像：
```bash
docker build -t nas-tools-chrome-novnc .
```

2. 运行容器：
```bash
docker run --shm-size=2g -p 9850:9850 -p 6080:6080 -d nas-tools-chrome-novnc
```

### 网页 VNC 访问

启动容器后，您可以通过网页 VNC 访问 Chrome 浏览器界面：

1. 打开浏览器并访问：
   ```
   http://localhost:6080
   ```

2. noVNC 界面将显示容器内运行的 Chrome 浏览器

3. 您可以监控浏览器活动，查看自动化脚本正在执行的操作

**端口说明：**
- `9850`: FastAPI 服务器端口
- `6080`: noVNC 网页界面端口
- `5900`: VNC 服务器端口（内部使用）

### 包安装

```bash
uv pip install -e .
```

## 使用方法

### 创建标签页

```bash
curl -X POST "http://localhost:9850/tabs/" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "tab_name": "example_tab",
    "cookie": "your_cookie_here"
  }'
```

### 获取 HTML 内容

```bash
curl "http://localhost:9850/tabs/example_tab/html"
```

### 点击元素

```bash
curl -X POST "http://localhost:9850/tabs/click/" \
  -H "Content-Type: application/json" \
  -d '{
    "tab_name": "example_tab",
    "selector": "#button-id"
  }'
```

## 配置

环境变量：
- `APP_HOST`: 服务器主机（默认：0.0.0.0）
- `APP_PORT`: 服务器端口（默认：9850）
- `CHROME_PATH`: 自定义 Chrome 浏览器路径

## 开发

### 运行测试

```bash
python -m pytest tests/
```

### 代码结构

项目遵循清晰架构模式：

- **src/config**: 应用配置和常量
- **src/core**: 核心业务逻辑和浏览器管理
- **src/api**: API 路由和请求/响应模式
- **src/utils**: 工具函数和辅助程序

## 许可证

GNU General Public License v3.0 (GPL-3.0) - 详见 LICENSE 文件。
