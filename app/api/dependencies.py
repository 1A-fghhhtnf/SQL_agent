from typing import Annotated

from async_lru import alru_cache
from fastapi.params import Depends
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manger
from app.repositories.es.value_es_repository import ValueInfoRepository
from app.repositories.mysql.dw_mysql_repository import DwMySQLRepository
from app.repositories.mysql.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.service.query_service import QueryService


@alru_cache
async def get_embedding_client()->HuggingFaceEndpointEmbeddings:
    return embedding_client_manager.client

@alru_cache
async def get_value_info_repository()->ValueInfoRepository:
    return ValueInfoRepository(es_client_manager.client)

@alru_cache
async def get_column_qdrant_repository()->ColumnQdrantRepository:
    return ColumnQdrantRepository(qdrant_client_manger.client)

@alru_cache
async def get_metric_qdrant_repository()->MetricQdrantRepository:
    return MetricQdrantRepository(qdrant_client_manger.client)

async def get_dw_session()->AsyncSession:
    #1.通过session_factory获取session
    async with dw_mysql_client_manager.session_factory() as session:
        try:
            #2.将session对象作为yield依赖项
            yield session
        finally:
            await session.aclose()

async  def get_dw_mysql_repository(session:Annotated[AsyncSession, Depends(get_dw_session)])->DwMySQLRepository:
    return DwMySQLRepository(session)


async def get_meta_session()->AsyncSession:
    async with meta_mysql_client_manager.session_factory() as session:
        try:
            yield session
        finally:
            await session.aclose()


async def get_meta_mysql_repository(session:Annotated[AsyncSession, Depends(get_meta_session)])->MetaMySQLRepository:
    return MetaMySQLRepository(session)


async def get_query_service(
        embedding_client:Annotated[HuggingFaceEndpointEmbeddings, Depends(get_embedding_client)],
        value_info_repository:Annotated[ValueInfoRepository, Depends(get_value_info_repository)],
        column_qdrant_repository:Annotated[ColumnQdrantRepository, Depends(get_column_qdrant_repository)],
        metric_qdrant_repository:Annotated[MetricQdrantRepository, Depends(get_metric_qdrant_repository)],
        dw_mysql_repository:Annotated[DwMySQLRepository, Depends(get_dw_mysql_repository)],
        meta_mysql_repository:Annotated[MetaMySQLRepository, Depends(get_meta_mysql_repository)],
    )->QueryService:
    return QueryService(
        embedding_client = embedding_client,
        value_info_repository=value_info_repository,
        column_qdrant_repository = column_qdrant_repository,
        metric_qdrant_repository=metric_qdrant_repository,
        dw_mysql_repository = dw_mysql_repository,
        meta_mysql_repository = meta_mysql_repository
    )