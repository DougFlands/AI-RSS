* 在 src/api/chat_api.py 中启动 Flask 应用：

`python src/api/chat_api.py`

或使用 `run.py` 启动：

`python run.py`

* 运行测试：

``` python
python -m unittest tests.test_api
python -m unittest tests.test_ai_chat
```

* 注意事项
依赖管理：确保安装了所需的 Python 包：

`pip install flask requests openai flask_mail feedparser`


https://github.com/weekend-project-space/top-rss-list

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_models/test_rss.py

# 生成覆盖率报告
pytest --cov-report html