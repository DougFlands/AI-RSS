# 第一阶段：构建前端
FROM node:24-slim AS frontend-builder

# 设置npm淘宝镜像
RUN npm config set registry https://registry.npmmirror.com

# 设置工作目录
WORKDIR /app/web

# 复制前端项目文件
COPY web/ ./

# 安装vite及所有依赖
RUN npm install

# 构建前端 - 创建构建脚本并运行
RUN echo 'import { build } from "./node_modules/vite/dist/node/index.js"; build();' > build.mjs && \
    node build.mjs

# 第二阶段：构建Python后端为二进制文件
FROM python:3.12-slim AS backend-builder

# 设置pip淘宝镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

# 设置apt中国镜像源 - 完全替换默认源配置
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo "deb https://mirrors.ustc.edu.cn/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.ustc.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.ustc.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y binutils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 安装pyinstaller和依赖
RUN pip install pyinstaller

# 设置工作目录
WORKDIR /app

# 复制Python项目依赖
COPY requirements.txt ./
RUN pip install  -r requirements.txt

# 复制Python源代码
COPY main.py ./
COPY app/ ./app/
COPY src/ ./src/
COPY tests/ ./tests/
COPY pytest.ini ./
COPY pyproject.toml ./

# 复制前一阶段构建的前端文件
COPY --from=frontend-builder /app/web/dist/ ./web/dist/

# 使用PyInstaller打包成二进制文件
RUN pyinstaller --onefile --name flask-ai-app --hidden-import=chromadb.telemetry.product.posthog --hidden-import=chromadb.api.fastapi main.py

# 第三阶段：创建最终镜像
FROM debian:bookworm-slim

# 设置工作目录
WORKDIR /app

# 直接复制Python和已安装的依赖包
COPY --from=backend-builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=backend-builder /usr/local/bin/python3.12 /usr/local/bin/python3.12
RUN ln -sf /usr/local/bin/python3.12 /usr/local/bin/python3

# 复制二进制可执行文件
COPY --from=backend-builder /app/dist/flask-ai-app ./

# 复制前端静态文件
COPY --from=frontend-builder /app/web/dist/ ./web/dist/

# 设置环境变量
ENV PYTHONPATH=/app

# 暴露应用端口
EXPOSE 5000

# 启动命令 - 修改为使用dotenv加载环境变量
# ENTRYPOINT ["./flask-ai-app"] 
CMD ["sh", "-c", "while :; do :; done"]