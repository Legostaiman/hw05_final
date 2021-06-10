import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TOKEN')
print(token)  # 123

account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("TOKEN")