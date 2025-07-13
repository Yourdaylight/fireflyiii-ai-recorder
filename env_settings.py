import os
import json
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    firefly_iii_url: str
    firefly_iii_api_key: str
    openai_api_base: str
    openai_api_key: str
    openai_model_name: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False

class UserConfigs():
    def __init__(self):
        self.configs = {}
        self.filepath = "user_configs.json"
        self.load()
    
    def load(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.configs = json.load(f)
        except FileNotFoundError:
            self.configs = {}
        except json.JSONDecodeError:
            self.configs = {}
        return self.configs
    
    def update(self, key, value):
        self.configs[key] = value
    
    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.configs, f, ensure_ascii=False, indent=4)
    
    def get(self, key, default=None):
        return self.configs.get(key, default)

def load_settings():
    try:
        # 尝试从 .env 文件加载
        return Settings()
    except Exception as e:
        print(f"Error loading from .env: {e}")
    
    try:
        # 尝试从环境变量加载
        return Settings(
            firefly_iii_url=os.getenv('FIREFLY_III_URL'),
            firefly_iii_api_key=os.getenv('FIREFLY_III_API_KEY'),
            openai_api_base=os.getenv('OPENAI_API_BASE'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            openai_model_name=os.getenv('OPENAI_MODEL_NAME')
        )
    except Exception as e:
        print(f"Error loading from environment variables: {e}")
        print("Please configure settings in one of the following ways:")
        print("1. Create a .env file with the following variables:")
        print("   FIREFLY_III_URL, FIREFLY_III_API_KEY, OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_MODEL_NAME")
        print("2. Set the above variables as environment variables")
        exit(1)

settings = load_settings()
