import argparse
import asyncio
from pathlib import Path

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manger
from app.repositories.es.value_es_repository import ValueInfoRepository
from app.repositories.mysql.dw_mysql_repository import DwMySQLRepository
from app.repositories.mysql.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.service.meta_knowledge_service import MetaKnowledgeService


async def build():
    #1.获取动态通过脚本参数传入：配置文件路径
    #1.1 方式一：采用argv方式获取脚本参数 列表中通过索引获取每个参数值 弊端：参数设置获取通过下标 argv[1]
    #1.2 方式二：采用argparse获取脚本参数
    #1.2.1 创建参数解析器对象
    parser = argparse.ArgumentParser(
        description="该脚本用于构建元数据知识库",
        usage="python -m app.scripts.build_meta_knowledge.py -c yaml文件路径",
        epilog="---------说明信息结束-----------------"
    )
    #1.2.2 设置短选项参数-c 或 长选型参数--conf
    parser.add_argument('-c', '--conf')
    #1.2.x 解析脚本参数方法 获取脚本参数值 结果是：Namespace对象 对象属性名称跟长选项参数名称一致
    args = parser.parse_args()
    meta_config_path = Path(args.conf)

    #2.调用业务层
    #2.1 执行各个客户端初始化操作
    dw_mysql_client_manager.init()
    meta_mysql_client_manager.init()
    embedding_client_manager.init()
    qdrant_client_manger.init()
    es_client_manager.init()

    #2.2 创建各个持久层对象
    async with (dw_mysql_client_manager.session_factory() as dw_session, meta_mysql_client_manager.session_factory() as meta_session):
        #2.3 创建业务层对象，通过构造注入各个持久层对象
        meta_knowledge_service = MetaKnowledgeService(
            dw_mysql_repository = DwMySQLRepository(dw_session),
            meta_mysql_repository = MetaMySQLRepository(meta_session),
            embedding_client=embedding_client_manager.client,
            column_qdrant_repository=ColumnQdrantRepository(qdrant_client_manger.client),
            value_info_repository = ValueInfoRepository(es_client_manager.client),
            metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manger.client),
        )
        #2.4 调用核心业务方法
        await meta_knowledge_service.build(meta_config_path)

        #3.提交事务，关闭各个客户端
        await meta_session.commit()

        await dw_mysql_client_manager.close()
        await meta_mysql_client_manager.close()
        await qdrant_client_manger.close()
        await es_client_manager.close()


if __name__ == '__main__':
    async def main():
        await build()
    asyncio.run(main())