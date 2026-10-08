from dataclasses import asdict

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

from app.conf.app_config import app_config
from app.entities.column_info import ColumnInfo


class ColumnQdrantRepository:

    COLLECTION_NAME="data-agent-column"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        """创建向量集合用于存放字段相关信息"""
        if not await self.client.collection_exists(collection_name=self.COLLECTION_NAME):
            await self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=app_config.qdrant.embedding_size,
                    distance=Distance.COSINE
                )
            )

    async def upsert(self, ids:list[str], payloads:list[ColumnInfo], embeddeds:list[list[float]], batch_size:int=10):
        """分批次保存向量点到qdrant"""
        #1. 通过zip函数将id、payload、embedded进行打包 按索引位置 转为元组列表 [(id1, payload1, embedded1), (id2, payload2, embedded2), ...
        zipped = list(zip(ids, payloads, embeddeds))
        #2. 分批次保存向量点
        for i in range(0, len(zipped), batch_size):
            batch = zipped[i:i + batch_size]
            await self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[PointStruct(
                    id=id,
                    payload=asdict(payload),
                    vector=embedded
                ) for id,payload,embedded in batch]
            )
