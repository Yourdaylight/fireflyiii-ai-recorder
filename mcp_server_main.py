# server.py
import asyncio
import aiohttp
import requests
import logging
from fastmcp import FastMCP
from typing import Annotated, Optional
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from firefly_api import FireflyIIIAPIClient
from env_settings import settings
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("FireflyTransactionRecorder")

# Create an MCP server
mcp = FastMCP("Firefly-Transaction-Recorder")

# Initialize API client
client = FireflyIIIAPIClient(
    base_url=settings.firefly_iii_url,
    api_key=settings.firefly_iii_api_key
)



async def record_expense(
    transactions: List[dict],
    dry_run: Optional[bool] = False
):
    """
    批量记录支出交易
    
    Args:
        transactions: 交易列表，每个交易包含以下字段:
            - description: 交易描述 (如"晚餐")
            - amount: 交易金额 (如256.0)
            - date: 交易日期（格式：YYYY-MM-DDT HH:mm，如"2025-05-25T11:49"）
            - category: 交易分类 (如"餐饮", 默认为"餐饮")
            - tags: 交易标签列表 (如["餐饮-晚餐"], 默认为根据分类匹配)
    """
    results = []
    categories = client.get_categories()
    existing_tags = client.get_tags()
    
    logger.info(f"开始处理 {len(transactions)} 笔交易")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx, transaction in enumerate(transactions, 1):
            logger.info(f"处理第 {idx} 笔交易: {transaction.get('description')}")
            # 设置默认值
            description = transaction.get('description')
            amount = transaction.get('amount')
            date = transaction.get('date', datetime.now().strftime("%Y-%m-%dT%H:%M"))
            category = transaction.get('category', "餐饮")
            tags = transaction.get('tags', [f"{category}-{description}"])
            
            # 验证分类和标签
            if category not in categories.values():
                error_msg = f"分类 '{category}' 不存在，分类可选项: {list(categories.values())}"
                logger.warning(f"交易验证失败: {error_msg}")
                results.append({
                    "error": error_msg,
                    "transaction": transaction
                })
                continue
                
            category_tags = [tag for tag in existing_tags.values() if tag.startswith(category)]
            if not all(tag in existing_tags.values() for tag in category_tags):
                error_msg = f"标签 '{tags}' 不存在，标签可选项: {list(category_tags.values())}"
                logger.warning(f"交易验证失败: {error_msg}")
                results.append({
                    "error": error_msg,
                    "transaction": transaction
                })
                continue
            
            logger.info(f"准备发送交易请求: {description}, 金额: {amount}, 分类: {category}")
            # 创建异步任务
            created_data = {
                        "error_if_duplicate_hash": False,
                        "apply_rules": False,
                        "fire_webhooks": True,
                        "group_title": description,
                        "transactions": [{
                            "type": "withdrawal",
                            "date": date,
                            "amount": str(amount),
                            "description": description,
                            "source_id": "1",
                            "source_name": "招行",
                            "reconciled": False,
                            "destination_id": "4",
                            "destination_name": "招行",
                            "category_name": category,
                            "tags": tags,
                            "foreign_amount": "0",
                            "foreign_currency_id": None,
                            "currency_id": "20",
                            "budget_id": 1
                        }]
                    }
            if dry_run:
                logger.info(f"Dry run: {created_data}")
                results.append({
                    "success": True,
                    "transaction": transaction,
                    "dry_run": True
                })
                continue
            task = asyncio.create_task(
                client._async_send_request(
                    session,
                    method="POST",
                    endpoint="/api/v1/transactions",
                    data=created_data
                )
            )
            tasks.append((transaction, task))
        
        # 等待所有任务完成
        for transaction, task in tasks:
            try:
                response = await task
                logger.info(f"交易处理成功: {transaction.get('description')}")
                results.append({
                    "success": True,
                    "response": response,
                    "transaction": transaction
                })
            except Exception as e:
                logger.error(f"交易处理失败: {str(e)}")
                results.append({
                    "error": str(e),
                    "transaction": transaction
                })
    
    success_count = len([r for r in results if r.get("success")])
    error_count = len([r for r in results if r.get("error")])
    logger.info(f"批量处理完成, 成功: {success_count} 笔, 失败: {error_count} 笔")
    return {
        "results": results,
        "success_count": success_count,
        "error_count": error_count
    }


if __name__ == "__main__":
    # Run the server
    mcp.run()
