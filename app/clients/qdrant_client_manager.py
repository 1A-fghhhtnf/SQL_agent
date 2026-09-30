import asyncio
import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct, QueryResponse, Filter, FieldCondition, \
    MatchValue

from app.clients.embedding_client_manager import embedding_client_manager
from app.conf.app_config import QdrantConfig, app_config


class QdrantClientManager:
    def __init__(self, config: QdrantConfig):
        self.config = config
        self.client: AsyncQdrantClient | None = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncQdrantClient(url=self._get_url())

    async def close(self):
        if self.client:
            await self.client.close()


qdrant_client_manger = QdrantClientManager(app_config.qdrant)

if __name__ == '__main__':
    qdrant_client_manger.init()
    qdrant_client = qdrant_client_manger.client

    embedding_client_manager.init()
    embedding_client = embedding_client_manager.client


    async def test():
        # 1.操作集合 判断集合是否存在，不存在则新建集合
        # flag = await qdrant_client.collection_exists(collection_name="test_collection1")
        # print("集合是否存在", flag)
        # if not flag:
        #     flag =await qdrant_client.create_collection(
        #         collection_name="test_collection1",
        #         vectors_config=VectorParams(
        #             size=app_config.qdrant.embedding_size,
        #             distance=Distance.COSINE
        #         )
        #     )
        #     print("创建集合", flag)
        #     await qdrant_client_manger.close()
        # 2. 操作向量点
        # await qdrant_client.upsert(
        #     collection_name="test_collection1",
        #     points=[PointStruct(
        #         id=uuid.uuid4(),
        #         payload={"category": "水果", "keyword": "苹果"},
        #         vector=await embedding_client.aembed_query("苹果")
        #     ), PointStruct(
        #         id=uuid.uuid4(),
        #         payload={"category": "水果", "keyword": "香蕉"},
        #         vector=await embedding_client.aembed_query("香蕉")
        #     ),PointStruct(
        #         id=uuid.uuid4(),
        #         payload={"category": "计算机", "keyword": "工程师"},
        #         vector=await embedding_client.aembed_query("工程师")
        #     )]
        # )
        # 3.相似度检索+元数据过滤
        result: QueryResponse = await qdrant_client.query_points(collection_name="test_collection1",
                                                                 query=await embedding_client.aembed_query("葡萄"),
                                                                 score_threshold=0.2,
                                                                 query_filter=Filter(
                                                                     must=[
                                                                         FieldCondition(
                                                                             key="category",
                                                                             match=MatchValue(value="水果"),
                                                                         )
                                                                     ]
                                                                 ),
                                                                 )
        points_result = [point.payload for point in result.points]
        print(points_result)
        await qdrant_client_manger.close()


    asyncio.run(test())
