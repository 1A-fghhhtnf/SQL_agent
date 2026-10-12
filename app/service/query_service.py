import json

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.state import DataAgentState
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manger
from app.repositories.es.value_es_repository import ValueInfoRepository
from app.repositories.mysql.dw_mysql_repository import DwMySQLRepository
from app.repositories.mysql.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class QueryService:

    def __init__(self,meta_mysql_repository:MetaMySQLRepository,dw_mysql_repository:DwMySQLRepository, column_qdrant_repository:ColumnQdrantRepository,metric_qdrant_repository:MetricQdrantRepository,embedding_client:HuggingFaceEndpointEmbeddings, value_info_repository:ValueInfoRepository):
        self.embedding_client = embedding_client
        self.value_info_repository = value_info_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.dw_mysql_repository = dw_mysql_repository
        self.meta_mysql_repository = meta_mysql_repository


    async def query(self, question:str):
        """
            根据问题生成SQL将查询结果响应
        :param question:
        :return:
        """
        #2.创建graph工作流节点需要封装静态依赖对象：
        context = DataAgentContext(
            dw_mysql_repository=self.dw_mysql_repository,
            meta_mysql_repository=self.meta_mysql_repository,
            embedding_client=self.embedding_client,
            value_info_repository=self.value_info_repository,
            column_qdrant_repository=self.column_qdrant_repository,
            metric_qdrant_repository=self.metric_qdrant_repository
        )
        #3.调用graph流式调用
        async for chunk in graph.astream(input=DataAgentState(query=question), context=context, stream_mode="custom"):
            #4.基于SSE协议响应chunk块的内容
            # json.dumps 将chunk转换为json字符串 ensure_ascii=False 解决中文"乱码问题" default=str 无法转JSON类型 转为字符串
            yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"

