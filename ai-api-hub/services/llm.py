import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-your-key-here"),
    base_url="https://api.deepseek.com/v1"
)
