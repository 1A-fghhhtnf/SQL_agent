from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manger
from app.core.log import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("项目启动，执行初始化操作...")
    # 初始化操作
    dw_mysql_client_manager.init()
    meta_mysql_client_manager.init()
    embedding_client_manager.init()
    es_client_manager.init()
    qdrant_client_manger.init()
    yield
    logger.info("项目关闭，执行清理操作...")
    # 关闭客户端
    await dw_mysql_client_manager.close()
    await meta_mysql_client_manager.close()
    await es_client_manager.close()
    await qdrant_client_manger.close()
