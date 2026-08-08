import os
from dotenv import load_dotenv

# 必须在 getenv 前面！
load_dotenv()  

env_url = os.getenv("TURSO_DATABASE_URL")
env_token = os.getenv("TURSO_AUTH_TOKEN")

print("env_url =", env_url)
print("env_token =", env_token)

if not env_url:
    raise SystemExit("错误：TURSO_DATABASE_URL 为空，请检查.env或者部署环境变量")
