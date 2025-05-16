import os
from dotenv import load_dotenv
load_dotenv()

def get_env_variable(name, default=None):
    value = os.getenv(name)

    if value is None:
        if default is not None:
            value = default
        else:
            return None  

    return value

EMAIL_SYSTEM_PROMPT="这是一段 RSS 信息，请将里面的信息过滤，按照你认为的重要程度排序并分类。最后输出一个 Email 的 HTML 正文。注意：邮件的正文需要包含标题和内容，标题需要包含日期，内容需要包含标题和链接，只输出 带HTML标签 的正文即可。不要输出 markdown "
RSS_SYSTEM_PROMPT="这是一段 RSS 信息，请根据标题、摘要、以及内容，进行优化表述。输出命名为 AITitle、AISummary，不需要 content，只需要这两个数据加link 链接，最后输出 JSON 格式。不要输出其他内容，请完整输出所有数据。"