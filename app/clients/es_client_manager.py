import asyncio

from elasticsearch import AsyncElasticsearch

from app.conf.app_config import ESConfig, app_config


class EsClientManager:

    def __init__(self, config: ESConfig):
        self.config = config
        self.client: AsyncElasticsearch | None = None


    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncElasticsearch(hosts=self._get_url())

    async def close(self):
        if self.client:
           await self.client.close()

es_client_manager = EsClientManager(app_config.es)


if __name__ == '__main__':
    es_client_manager.init()
    es_client = es_client_manager.client

    async def test_index():
        result = await es_client.indices.exists(index="product")
        if not result:
            response = await es_client.indices.create(
                index="product",
                mappings={
                    "properties": {
                        "id":{
                            "type": "integer"
                        },
                        "title":{
                            "type": "text",
                            "analyzer": "ik_max_word"
                        },
                        "brand":{
                            "type": "keyword"
                        },
                        "price":{
                            "type": "integer"
                        },
                        "image":{
                            "type": "keyword",
                            "index": False
                        }
                    }
                }
            )
            print(response)
        await es_client_manager.close()

    # asyncio.run(test_index())

    async def test_doc():
        # respose= await es_client.index(
        #     index="product",
        #     document={
        #       "id": 3,
        #       "title": "苹果笔记本电脑",
        #       "brand": "苹果",
        #       "price": 9700,
        #       "image":"apple.png"
        #     }
        # )
        # print(respose)
        # 批量插入
        await es_client.bulk(
            operations=[
                {"index": {"_index": "product"}},
                {"title": "华为问界汽车", "brand": "华为问界", "price": 5555500, "image": "wj.png"},
                {"index": {"_index": "product", "_id": "1"}},
                {"title": "苹果手机IPhone18白色最新款1TB国庆节大促销", "brand": "苹果", "price": 100000,
                 "image": "apple.png"}
            ]
        )
        # await es_client_manager.close()
    asyncio.run(test_doc())