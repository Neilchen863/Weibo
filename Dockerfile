# 基础镜像：用官方 Python 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖和项目代码
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 默认运行命令（你可以换成 weibo_spider.py，如果它是主入口）
CMD ["python", "main.py"]
