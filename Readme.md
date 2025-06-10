# RSS阅读器应用

这是一个基于Flask和Vue3的RSS阅读器应用，具有以下功能：

- 从RSS源获取最新内容
- 使用Chroma向量数据库存储RSS内容
- 支持搜索功能，查找感兴趣的内容
- 支持对RSS内容标记喜欢/不喜欢
- 不喜欢时可以添加原因，保存到MongoDB
- 基于用户喜好对RSS内容进行智能排序

## 环境要求

- Python 3.8+
- Node.js 16+
- MongoDB
- Chroma向量数据库

## 安装与运行

### 安装后端依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建`.env`文件或使用系统环境变量设置以下内容：

```
DEBUG_MODE=True
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=rss_app
START_SERVER_SEND_MAIL=False
MAIL_RECIPIENTS=your-email@example.com
```

### 构建前端

```bash
cd vue_app
npm install
npm run build
```

### 运行应用

```bash
python main.py
```

## 使用方法

访问 http://localhost:5000 即可使用RSS阅读器。

- 使用搜索框可以搜索特定内容
- 点击"喜欢"/"不喜欢"按钮标记偏好
- 选择"不喜欢"时可以输入原因
- 使用筛选按钮可以筛选不同类型的内容

## 架构说明

- 后端：Flask API，提供RSS获取、搜索和偏好存储功能
- 存储：Chroma向量数据库(RSS内容)和MongoDB(用户偏好)
- 前端：Vue3 + Element Plus构建的现代化界面

一个 AI 分析 RSS 的工具

1. 自动分类订阅的 RSS
2. 将 RSS 信息发送到指定邮箱，默认早9晚6发送
3. 使用 langchian 接入 ollama 本地模型或 coze 平台模型(推荐)
4. 配置 langsmith 可查看详细数据

* 注意事项
依赖管理：确保安装了所需的 Python 包：

`pip install flask requests openai flask_mail feedparser`

# rss 示例
https://github.com/weekend-project-space/top-rss-list

# 接口文档
https://apifox.com/apidoc/shared-d9df3dbf-6f83-480d-ae0c-fdc7c65ab8aa


pip install sentry_sdk

podman build -f .\Dockerfile -t rss-ai
podman run --env-file ./production.env -p 5000:5000 rss-ai

注意:
1. production.env 里只有 key=value, value 不能有引号

podman run -i --rm -e CHROMA_CLIENT_TYPE=http -e CHROMA_HOST=10.11.12.10 -e CHROMA_PORT=48000 -e CHROMA_SSL=false mcp/chroma