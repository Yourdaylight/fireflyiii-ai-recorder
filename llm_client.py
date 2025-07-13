from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.chat_models import init_chat_model
from firefly_api import FireflyIIIAPIClient
from env_settings import settings
from typing import List, Dict
from cache import global_cache

class FireflyTransactionAgent:
    def __init__(self):
        self.llm = init_chat_model(
            "deepseek-chat",
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
            model_provider="deepseek",
        )
        self.firefly = FireflyIIIAPIClient(
            base_url=settings.firefly_iii_url,
            api_key=settings.firefly_iii_api_key
        )
        self.parser = JsonOutputParser()
        self.prompt = self.generate_prompt("")
        self.chain = self.prompt | self.llm | self.parser
    
    def generate_prompt(self, text: str) -> str:

        self.prompt = ChatPromptTemplate.from_template("""
            请将以下交易记录文本解析为JSON数组格式，要求包含以下字段：
            - date: 交易日期（格式：YYYY-MM-DDTHH:mm）
            - description: 交易描述
            - amount: 交易金额
            - category: 交易分类
            - tags: 交易标签列表
            - think_result: AI的思考结果
            交易的分类你需要根据用户输入内存中的描述，从{categories}中选择合适的分类[category]，然后从{tags}中选择合适的一个标签，标签必须以刚刚选择出来的[category]开头，如果无法匹配则可以以这个规则新建一个。
            示例输入：
            07.06
            - 12.00 午餐 66
            - 16.00 物业费 900
            
            示例输出：
            {{
                "transactions": [
                    {{
                        "date": "2025-07-06T12:00",
                        "description": "午餐",
                        "amount": 66,
                        "category": "餐饮",
                        "tags": ["餐饮-午餐"]
                    }},
                    {{
                        "date": "2025-07-06T16:00",
                        "description": "物业费", 
                        "amount": 900,
                        "category": "居家",
                        "tags": ["居家-物业费"]
                    }}
                ]
                "think_result": "展现AI的思考过程与总结结果"
            }}
            
            实际输入：
            {input_text}
        """)
        return self.prompt

    def get_tags_and_categories(self) -> Dict[str, List[str]]:
        """获取Firefly III的分类和标签"""
        cached = global_cache.get("tags_and_categories")
        if cached:
            print("使用缓存的分类和标签")
            return cached
        categories = self.firefly.get_categories()
        tags = self.firefly.get_tags()
        categories_and_tags = {
            "tags": tags,
            "categories": categories
        }
        global_cache.set("tags_and_categories", categories_and_tags)
        return categories_and_tags
    def parse(self, text: str) -> Dict:
        try:
            tags_and_categories = self.get_tags_and_categories()
            categories = tags_and_categories.get("categories", [])
            tags = tags_and_categories.get("tags", [])
            result = self.chain.invoke({"input_text": text, "categories": categories, "tags": tags})
            return {
                "transactions": result.get("transactions", []),
                "think_result": result.get("think_result", "AI思考结果未返回")
            }
        except Exception as e:
            print(f"解析失败: {str(e)}")
            return {"transactions": [], "think_result": f"解析失败: {str(e)}"}

if __name__ == "__main__":
    parser = FireflyTransactionAgent()
    test_text = """07.06
    - 12.00 午餐 66
    - 16.00 物业费 900
    - 18.00 水果 10
    """
    print(parser.parse(test_text))
