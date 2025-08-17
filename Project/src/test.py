# test_openai_key_new.py

import os
from openai import OpenAI, AuthenticationError, APIConnectionError

# 读取 API Key（推荐从环境变量中读取）
api_key = "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"

client = OpenAI(api_key=api_key)

def test_key():
    try:
        models = client.models.list()
        print("✅ API Key 有效，当前可用模型：")
        for model in models.data:
            print(" -", model.id)
    except AuthenticationError:
        print("❌ API Key 无效或未授权。请检查 key 是否正确。")
    except APIConnectionError:
        print("❌ 无法连接到 OpenAI API。请检查网络或代理设置。")
    except Exception as e:
        print("❌ 发生未知错误：", e)

if __name__ == "__main__":
    test_key()