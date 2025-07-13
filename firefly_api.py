import aiohttp
import requests
from typing import Dict, Any

class FireflyIIIAPIClient:
    """Firefly III API 调用客户端"""
    
    def __init__(self, base_url: str, api_key: str):
        """
        初始化客户端
        
        :param base_url: API 基础地址（例如：https://api.firefly-iii.org）
        :param api_key: 身份验证API密钥（若需要）
        """
        self.base_url = base_url.rstrip('/')  # 确保基础地址格式正确
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"  # 示例：Bearer认证方式，可根据实际调整
        }

    async def _async_send_request(self, session: aiohttp.ClientSession, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Any:
        """
        异步发送HTTP请求的通用方法
        
        :param session: aiohttp会话
        :param method: 请求方法（GET/POST/PUT/DELETE等）
        :param endpoint: 接口路径（例如：/api/v1/accounts）
        :param params: 查询参数（GET请求使用）
        :param data: 请求体数据（POST/PUT请求使用）
        :return: 接口响应数据（JSON格式）
        :raises: 请求异常时抛出HTTPError
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            async with session.request(
                method=method.upper(),
                url=url,
                headers=self.headers,
                params=params,
                json=data
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            print(f"异步API请求失败：{e}")
            raise

    def _send_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Any:
        """
        同步发送HTTP请求的通用方法
        
        :param method: 请求方法（GET/POST/PUT/DELETE等）
        :param endpoint: 接口路径（例如：/api/v1/accounts）
        :param params: 查询参数（GET请求使用）
        :param data: 请求体数据（POST/PUT请求使用）
        :return: 接口响应数据（JSON格式）
        :raises: 请求异常时抛出HTTPError
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=self.headers,
                params=params,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API请求失败：{e}")
            raise

    # ====================== 接口方法（需根据实际API文档修改）======================
    def get_accounts(self) -> Dict:
        """示例：获取账户列表（假设存在GET /api/v1/accounts接口）"""
        return self._send_request(method="GET", endpoint="/api/v1/accounts")

    def create_transaction(self, data: Dict) -> Dict:
        """示例：创建交易（假设存在POST /api/v1/transactions接口）"""
        return self._send_request(method="POST", endpoint="/api/v1/transactions", data=data)
    
    def get_categories(self,limit=100, simple_return=True) -> Dict:
        """
        示例：获取分类列表（假设存在GET /api/v1/categories接口）
        :param simple_return: 是否返回简化的分类名称列表（默认为True）
        :return: 分类列表（字典格式）如果simple_return为True，则返回{分类ID: 分类名称}的字典，否则返回完整的分类信息
        """
        categories = self._send_request(method="GET", endpoint="/api/v1/categories", params={"limit": limit})
        if categories and simple_return:
            # 提取分类名称
            return {category["id"]: category["attributes"]["name"] for category in categories["data"]}
        else:
            # 返回完整的分类信息
            return categories
    
    def get_tags(self, limit=500, simple_return=True) -> Dict:
        """
        示例：获取标签列表（假设存在GET /api/v1/tags接口）
        :param simple_return: 是否返回简化的标签名称列表（默认为True）
        :return: 标签列表（字典格式）如果simple_return为True，则返回{标签ID: 标签名称}的字典，否则返回完整的标签信息
        """
        tags = self._send_request(method="GET", endpoint="/api/v1/tags", params={"limit": limit})
        if tags and simple_return:
            # 提取标签名称
            return {tag["id"]: tag["attributes"]["tag"] for tag in tags["data"]}
        else:
            # 返回完整的标签信息
            return tags
    def get_accounts(self, limit=100):
        """
        获取账户列表
        
        :param limit: 返回的账户数量限制（默认为100）
        :return: 账户字典，格式为:
            {
                "id": {
                    "name": "账户名",
                    "type": "账户类型(cash/revenue/expense/asset)",
                    "account_role": "角色",
                    "current_balance": "当前余额",
                    "links": "API链接"
                },
                ...
            }
        """
        accounts = self._send_request(method="GET", endpoint="/api/v1/accounts", params={"limit": limit})
        simplified_accounts = {}
        for account in accounts.get("data", []):
            account_id = account["id"]
            account_attrs = account["attributes"]
            simplified_accounts[account_id] = {
                "name": account_attrs["name"],
                "type": account_attrs["type"],
                "account_role": account_attrs.get("account_role"),
                "current_balance": f'{account_attrs["currency_symbol"]} {account_attrs["current_balance"]}',
                "links": account["links"]["self"],
            }
        return simplified_accounts
    
    def get_latest_transactions(self, limit=100) -> Dict:
        """
        获取最新交易记录
        
        :param limit: 返回的交易数量限制（默认为100）
        :return: 交易列表，格式为:
            {
                "id": {
                    "date": "交易日期",
                    "amount": "交易金额",
                    "description": "交易描述",
                    "category": "分类名称",
                    "tags": ["标签1", "标签2"],
                    "notes": "备注信息"
                },
                ...
            }
        """
        transactions = self._send_request(method="GET", endpoint="/api/v1/transactions", params={"limit": limit})
        simplified_transactions = {}
        for transaction in transactions.get("data", []):
            transaction_id = transaction["id"]
            transaction_attrs = transaction["attributes"]
            transaction_item = transaction_attrs.get("transactions")[0]
            simplified_transactions[transaction_id] = {
                "date": transaction_item.get("date"),
                "amount": f"{transaction_item.get('currency_symbol')} {transaction_item.get('amount')}",
                "description": transaction_item.get("description"),
                "category_name": transaction_item.get("category_name"),
                "category_id": transaction_item.get("category_id"),
                "tags": transaction_item.get("tags", []),
                "source_id": transaction_item.get("source_id"),
                "destination_id": transaction_item.get("destination_id"),
            }
        return simplified_transactions
    def create_transaction_with_template(
        self,
        transaction_type: str,
        date: str,
        amount: str,
        description: str,
        category_name: str = "餐饮",  # 默认值
        tags: list = None,       # 可选标签列表
        notes: str = None,   # 可选备注
        destination_id: str="4",      # 默认值
        destination_name: str="招行", # 默认值
    ) -> Dict:
        """
        按固定模板创建交易（支出场景）
        
        :param transaction_type: 交易类型（需为"withdrawal"）
        :param date: 交易日期（格式：YYYY-MM-DDT HH:mm，如"2025-05-25T11:49"）
        :param amount: 交易金额（字符串格式，如"8"）
        :param description: 交易描述（如"午餐"）
        :param destination_id: 目标账户ID（如"4"）
        :param destination_name: 目标账户名称（如"支出"）
        :param category_name: 交易类别（默认值："餐饮"，可修改）
        :param tags: 标签列表（可选，如["餐饮-午餐"]）
        :param notes: 交易备注（可选）
        :return: API响应数据
        :raises: ValueError 当交易类型非"withdrawal"时抛出
        """
        # 校验交易类型（支出场景固定为withdrawal）
        if transaction_type.lower() != "withdrawal":
            raise ValueError("支出场景下交易类型必须为'withdrawal'")
        
        # 构造固定参数（按模板要求填充）
        fixed_params = {
            "error_if_duplicate_hash": False,
            "apply_rules": False,
            "fire_webhooks": True,
            "group_title": description,
            "transactions": [
                {
                    "type": transaction_type,
                    "date": date,
                    "amount": amount,
                    "description": description,
                    "source_id": "1",          # 固定值（支出场景来源账户）
                    "source_name": "招行",      # 固定值
                    "reconciled": False,
                    "destination_id": destination_id,
                    "destination_name": destination_name,
                    "category_name": category_name,
                    "interest_date": None,
                    "book_date": None,
                    "process_date": None,
                    "due_date": None,
                    "payment_date": None,
                    "invoice_date": None,
                    "internal_reference": None,
                    "external_url": None,
                    "notes": notes,            # 可选备注
                    "tags": tags or ["餐饮-午餐"],  # 默认为["餐饮-午餐"]，可覆盖
                    "foreign_amount": "0",     # 固定值
                    "foreign_currency_id": None,  # 固定值
                    "currency_id": "20",       # 固定值（货币ID）
                    "budget_id": 1             # 固定值（预算ID）
                }
            ]
        }
        
        # 发送请求
        return self._send_request(
            method="POST",
            endpoint="/api/v1/transactions",  # 假设接口路径为POST /api/v1/transactions
            data=fixed_params
        )



# ====================== 使用示例 ======================
if __name__ == "__main__":
    # 初始化客户端（请替换为实际API地址和密钥）
    from env_settings import settings

    client = FireflyIIIAPIClient(
        base_url=settings.firefly_iii_url,
        api_key=settings.firefly_iii_api_key
    )
    
    # 调用示例接口
    try:
        categories = client.get_categories()
    
        accounts = client.get_latest_transactions(limit=10)
        print("账户列表：", accounts)
    except Exception as e:
        print(f"操作失败：{e}")
