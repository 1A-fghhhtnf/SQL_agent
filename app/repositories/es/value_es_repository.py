from dataclasses import asdict

from elasticsearch import AsyncElasticsearch

from app.entities.value_info import ValueInfo


class ValueInfoRepository:
    INDEX_NAME = "data-agent-column"
    ES_INDEX_MAPPINGS = {
        "dynamic": False,
        "properties": {
            "id": {"type": "keyword"},
            "value": {"type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_max_word"},
            "column_id": {"type": "keyword"}
        }
    }

    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def ensure_index(self):
        """采用显式映射创建索引库"""
        if not await self.client.indices.exists(index=self.INDEX_NAME):
            await self.client.indices.create(
                index=self.INDEX_NAME,
                mappings=self.ES_INDEX_MAPPINGS
            )

    async def upsert(self, value_infos: list[ValueInfo], batch_size: int = 10):
        """
        批量新增文档到ES索引库
        :param value_infos:
        :return:
        """
        for i in range(0, len(value_infos), batch_size):
            operations = []
            batch = value_infos[i: i + batch_size]
            for value_info in batch:
                operations.append({
                    "index": {
                        "_index": self.INDEX_NAME,
                        "_id": value_info.id
                    }
                })
                operations.append(asdict(value_info))
            await self.client.bulk(operations=operations)
