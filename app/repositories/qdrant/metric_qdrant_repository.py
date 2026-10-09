from dataclasses import asdict

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct, QueryResponse, QueryRequest

from app.conf.app_config import app_config
from app.entities.metric_info import MetricInfo


class MetricQdrantRepository:
    COLLECTION_NAME = "data-agent-metric"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        """创建向量集合用于存放指标相关信息"""
        if not await self.client.collection_exists(collection_name=self.COLLECTION_NAME):
            await self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=app_config.qdrant.embedding_size,
                    distance=Distance.COSINE
                )
            )

    async def upsert(self, ids: list[str], payloads: list[MetricInfo], embeddeds: list[list[float]],
                     batch_size: int = 10):
        # 1.通过zip函数按索引位置进行打包得到元祖列表
        zipped = list(zip(ids, payloads, embeddeds))
        # 2.分批次构建向量点对象，批量新增
        for i in range(0, len(zipped), batch_size):
            batch = zipped[i:i + batch_size]
            points = [PointStruct(
                id=id,
                payload=asdict(payload),
                vector=embedded
            ) for id,payload,embedded in batch]
            await self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=points
            )

    async def search(self, vector:list[float], score_threshold:float=0.6, limit:int=10)->list[MetricInfo]:
        """根据向量搜索相似的指标"""
        result:QueryResponse = await self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=vector,
            score_threshold=score_threshold,
            limit=limit
        )
        return [MetricInfo(**point.payload) for point in result.points]

    async def search_batch(self, vectors:list[list[float]],score_threshold:float=0.6, limit:int=10)->list[MetricInfo]:
        """根据向量批量搜索相似的指标"""
        # 将每个向量转为QueryRequest对象得到QueryRequest列表
        query_requests:list[QueryRequest] = [QueryRequest(
            query=vector,
            with_payload=True,
            score_threshold=score_threshold,
            limit=limit
        ) for vector in vectors]
        results:list[QueryResponse] = await self.client.query_batch_points(
            collection_name=self.COLLECTION_NAME,
            requests=query_requests
        )
        return [MetricInfo(**point.payload) for result in results for point in result.points]
