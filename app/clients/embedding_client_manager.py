import asyncio

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddingClientManager:

    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.client: HuggingFaceEndpointEmbeddings | None = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = HuggingFaceEndpointEmbeddings(model=self._get_url())


# 对外提供embedding客户端管理器对象 用于向量操作
embedding_client_manager = EmbeddingClientManager(app_config.embedding)

if __name__ == '__main__':
    embedding_client_manager.init()
    client = embedding_client_manager.client


    async def test_embedding():
        # 1.同步对单个文本转为向量 list[float]  IO 程序阻塞 性能差
        # print(client.embed_query("你好"))
        # 2.同步对多个文本转为向量 list[list[float]]
        # print(client.embed_documents(["计算机", "笔记本电脑"]))

        #3. 异步方式
        print(await client.aembed_query("葡萄"))
        # print(await client.aembed_documents(["计算机", "笔记本电脑"]))

        #4. 场景：N多文本需要转为向量 采用分批次处理 例如：每次处理5个
        # embeddings = []
        # texts = ["计算机", "笔记本电脑", "手机", "平板电脑", "智能手环", "智能手表", "智能音箱", "智能门锁", "智能摄像头", "智能插座", "智能灯泡"]
        # batch_size = 5
        # for i in range(0, len(texts), batch_size):
        #     # 获取当前批次需要处理数据
        #     batch_texts = texts[i:i+batch_size]
        #     batch_embedded = await client.aembed_documents(batch_texts)
        #     embeddings.extend(batch_embedded)

    asyncio.run(test_embedding())
