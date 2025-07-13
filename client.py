
import json
import uvicorn
import asyncio
import traceback
from typing import List
from fastapi import FastAPI, Request, HTTPException, Body, Response
from typing import Dict, List
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from cache import global_cache as cache
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from env_settings import settings, UserConfigs
from llm_client import FireflyTransactionAgent
from firefly_api import  FireflyIIIAPIClient
from collections import Counter
VERSION = "0.1.2"
app = FastAPI()
import os

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 配置静态文件和模板
static_dir = os.path.join(current_dir, "static")
templates_dir = os.path.join(current_dir, "templates")

# 打印静态文件目录路径用于调试
print(f"静态文件目录: {static_dir}")

# 检查静态文件目录是否存在
if not os.path.exists(static_dir):
    print(f"错误: 静态文件目录不存在: {static_dir}")
else:
    print(f"静态文件目录存在，包含文件: {os.listdir(static_dir)}")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

firefly =  FireflyIIIAPIClient(
    base_url=settings.firefly_iii_url,
    api_key=settings.firefly_iii_api_key
)

# 自定义中间件：记录请求和响应
@app.middleware("http")
async def log_middleware(request: Request, call_next):
    # 特殊处理：如果请求路径是/static或/static/，则重写为/
    print(f"接收到请求: {request.url.path}")
    if request.url.path in ["/static", "/static/"]:
        # 直接修改请求的路径
        request.scope["path"] = "/"
        request.scope["raw_path"] = b"/"
        print(f"重写请求: {request.url} -> /")
    
    # 记录请求信息
    print(f"请求: {request.method} {request.url}")
    
    # 调用下一个中间件或路由处理函数
    response = await call_next(request)
    
    # 记录响应信息
    print(f"响应状态码: {response.status_code}")
    
    # 读取并记录响应体
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk
    
    # 重新构造响应（因为响应体已被读取）
    response = Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type
    )
    
    # 打印响应体（如果是文本类型）
    if response.media_type and (response.media_type.startswith("text/") or response.media_type == "application/json"):
        try:
            body_str = response_body.decode("utf-8")
            print(f"响应体: {body_str}")
        except UnicodeDecodeError:
            print("响应体: (二进制内容，不打印)")
    
    return response

@app.get("/", response_class=HTMLResponse)
@app.get("/static", response_class=HTMLResponse)
@app.get("/static/", response_class=HTMLResponse)
async def web_interface(request: Request):
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/parse")
async def parse_transactions(text: str = Body(...)):
    try:

        parser = FireflyTransactionAgent()
        transactions = parser.parse(text)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/record")
async def record_transaction(transactions: List[dict]):
    try:
        # 使用settings中的配置
        from mcp_server_main import record_expense
        result = await record_expense(transactions, dry_run=False)
        return {"message": "Transaction recorded successfully","result": result}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tags-and-categories")
async def get_tags_and_categories():
    cached = cache.get("tags_and_categories")
    if cached:
        return cached
        
    categories = firefly.get_categories()
    tags = firefly.get_tags()
    result = {
        "categories": list(categories.values()),
        "tags": list(tags.values())
    }
    
    cache.set("tags_and_categories", result)
    return result

@app.get("/api/accounts")
async def get_accounts():
    cached = cache.get("accounts")
    if cached:
        return cached
        
    try:
        accounts = firefly.get_accounts()
        cache.set("accounts", accounts)
        return accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户列表失败: {str(e)}")


@app.get("/api/transactions")
async def get_transactions():
    try:
        if cache.get("transactions"):
            return cache.get("transactions")
        latest_tarnsactions = firefly.get_latest_transactions()
        if latest_tarnsactions:
            cache.set("transactions", latest_tarnsactions)
        return latest_tarnsactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最新交易失败: {str(e)}")

@app.get("/api/default_account")
async def get_default_account():
    user_configs = UserConfigs()
    default_revenue_account = user_configs.get("default_revenue")
    default_expense_account = user_configs.get("default_expense")
    if default_revenue_account == str(-1) or default_expense_account == str(-1):
        latest_tarnsactions = firefly.get_latest_transactions()
        source_ids = [t["source_id"] for t in latest_tarnsactions.values()]
        destination_ids = [t["destination_id"] for t in latest_tarnsactions.values()]
        # 出现最多的账户作为默认账户
        default_revenue_account = Counter(destination_ids).most_common(1)[0][0] #支出目标账户
        default_expense_account = Counter(source_ids).most_common(1)[0][0] #支出源账户
        user_configs.update("default_revenue", default_revenue_account)
        user_configs.update("default_expense", default_expense_account)
        user_configs.save()
    default_configs = user_configs.configs
    default_configs["version"] = VERSION
    default_configs["firefly_iii_url"] = settings.firefly_iii_url
    return default_configs

@app.post("/api/default")
async def update_user_config(data: dict = Body(...)):
    try:
        user_configs = UserConfigs()
        for key, value in data.items():
            user_configs.update(key, value)
        user_configs.save()
        return {"message": "用户配置更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户配置失败: {str(e)}")

def run_web_server():
    config = uvicorn.Config(app, host="0.0.0.0", port=5001)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())

if __name__ == "__main__":
    run_web_server()
