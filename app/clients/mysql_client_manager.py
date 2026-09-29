import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession

from app.conf.app_config import DBConfig, app_config


class MysqlClientManager:
    """myslq客户端管理器，操作dw,meta库都需要通过该类实例产生引擎"""

    def __init__(self, db_config: DBConfig):
        self.db_config = db_config
        self.engine: AsyncEngine | None = None

    def _get_url(self):
        return f"mysql+asyncmy://{self.db_config.user}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}?charset=utf8mb4"

    def init(self):
        self.engine = create_async_engine(url=self._get_url(), echo=False,  # 设置连接池最大空闲连接数
            pool_size=10,  pool_pre_ping=True)

# 对外提供单例对象 dw、meta 库数据库管理客户端
dw_mysql_client_manager = MysqlClientManager(app_config.db_dw)
meta_mysql_client_manager = MysqlClientManager(app_config.db_meta)

if __name__ == '__main__':
    dw_mysql_client_manager.init()

    async def test_dw():
        async with AsyncSession(dw_mysql_client_manager.engine) as session:
            # 执行自定义SQL
            result = await session.execute(text("select 1"))
            # 单列单行结果 .scalar() 方法返回单个结果
            print(result.scalar())
    asyncio.run(test_dw())