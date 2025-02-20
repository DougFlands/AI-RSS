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

# 测试
## 运行所有测试
pytest

## 运行特定测试文件
pytest tests/test_models/test_rss.py

## 生成覆盖率报告
pytest --cov-report html