# 第一阶段：构建前端
FROM node:24-slim AS frontend-builder

# 第二阶段：构建Python后端为二进制文件
FROM python:3.12-slim AS backend-builder

# 第三阶段：创建最终镜像
FROM debian:bookworm-slim
