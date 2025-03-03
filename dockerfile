# 使用 Python 官方镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件到工作目录
COPY ./requirements.txt ./requirements.txt


# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件到工作目录
COPY . .



# 暴露应用程序运行的端口
EXPOSE 5000

# 定义启动命令
CMD ["python", "main.py"]