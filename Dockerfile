# 使用官方Python镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装必要的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install  --no-cache-dir -r requirements.txt --trusted-host mirrors.aliyun.com -i http://mirrors.aliyun.com/pypi/simple/

# 复制应用代码
COPY .env.example cache.py client.py firefly_api.py mcp_server_main.py  llm_client.py ./
COPY static/ static/
COPY templates/ templates/
COPY env_settings.py user_configs.json ./

# 暴露端口
EXPOSE 5001

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV FIREFLY_III_URL="http://192.168.1.6:8888"
ENV OPENAI_API_BASE="https://api.deepseek.com"
ENV OPENAI_MODEL_NAME="deepseek-chat"

# 说明：敏感变量(FIREFLY_III_API_KEY, OPENAI_API_KEY)应通过以下方式配置：
# 1. Docker Desktop环境变量配置界面
# 2. 运行时通过-e参数传递
# 3. 通过.env文件挂载到容器

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:5001/ || exit 1

# 启动命令
CMD ["uvicorn", "client:app", "--host", "0.0.0.0", "--port", "5001", "--reload"]
