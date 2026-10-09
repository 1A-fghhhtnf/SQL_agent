import asyncio

from langchain.chat_models import init_chat_model

from app.conf.app_config import app_config

llm = init_chat_model(
    model=app_config.llm.model_name,
    api_key=app_config.llm.api_key,
    base_url=app_config.llm.base_url,
    temperature=0,
)

if __name__ == '__main__':
    # result = llm.invoke("介绍下自己")
    # print(result.content)

    async def test():
        result = await llm.ainvoke("介绍下自己")
        print(result.content)
    asyncio.run(test())
