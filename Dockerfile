# 基础镜像：用官方 Python 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖和项目代码
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 暴露网页端口
EXPOSE 8000

# 以网页服务启动（FastAPI + uvicorn）
CMD ["uvicorn", "webapp:app", "--host", "0.0.0.0", "--port", "8000"]
