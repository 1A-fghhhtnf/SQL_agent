import asyncio

from sqlalchemy import text, update, Result
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession, async_sessionmaker
from watchfiles import awatch

from app.conf.app_config import DBConfig, app_config
from app.models.table_info_mysql import TableInfoMySQL


class MysqlClientManager:
    """myslq客户端管理器，操作dw,meta库都需要通过该类实例产生引擎"""

    def __init__(self, db_config: DBConfig):
        self.db_config = db_config
        self.engine: AsyncEngine | None = None
        # async_sessionmaker 是类 用于产生session工厂类
        self.session_factory: async_sessionmaker|None =None

    def _get_url(self):
        return f"mysql+asyncmy://{self.db_config.user}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}?charset=utf8mb4"

    def init(self):
        self.engine = create_async_engine(url=self._get_url(), echo=True,  # 设置连接池最大空闲连接数
            pool_size=10,  pool_pre_ping=True)
        # 基于引擎对象产生session工厂对象 默认事务自动开启
        self.session_factory = async_sessionmaker(bind=self.engine, autobegin=True,autoflush=True, expire_on_commit=True)

    async def close(self):
        if self.engine:
            await self.engine.dispose()
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
    # asyncio.run(test_dw())

    async def test_dw_session_factory():
        async with dw_mysql_client_manager.session_factory() as dw_session:
            # 执行自定义SQL
            # result = await dw_session.execute(text("select 1"))
            # 单列单行结果 .scalar() 方法返回单个结果
            # print(result.scalar())
            # result:Result = await dw_session.execute(text("select order_id from fact_order"))
            # 单例多行结果.result.scalars().fetchall()
            # print(result.scalars().fetchall())

            result:Result = await dw_session.execute(text("select * from fact_order"))
            # 多列多行 [(列1值,列2值....),()]
            # print(result.fetchall())
            # 提取单行数据
            # print(result.fetchone())
            #[{'字段名称':列值,'字段名称':列值}]
            print(result.mappings().fetchall())


    asyncio.run(test_dw_session_factory())

    meta_mysql_client_manager.init()

    async def test_meta_session():
        async with meta_mysql_client_manager.session_factory() as meta_session:
            #1.需求新增表信息记录到table_info表 默认不需要开启事务，事务自动开启
            # table_info_mysql=TableInfoMySQL(
            #     id="fact_order1",
            #     name="fact_order",
            #     role="fact",
            #     description="订单事实表"
            # )
            # meta_session.add(table_info_mysql)
            # 2.需求修改
            # stmt = (
            #     update(TableInfoMySQL).where(TableInfoMySQL.id == 'fact_order1').values(description="该表中存放的是订单事实表相关数据")
            # )
            # await meta_session.execute(stmt)
            # orm_model:TableInfoMySQL = await meta_session.get(TableInfoMySQL, "fact_order1")
            # print(orm_model.description)

            # 演示expire_on_commit=False 查询后提交事务输出对象中属性值 并未执行SQL，性能高，并发写场景写会读到脏数据
            # 演示expire_on_commit=True 报错：MissingGreenlet 解决方法meta_session.refresh(orm_model) 再次执行查询SQL获取；保证返回最新数据
            orm_model:TableInfoMySQL = await meta_session.get(TableInfoMySQL, "fact_order1")
            #2.提交事务
            await meta_session.commit()
            # expire_on_commit=True 需要刷新ORM对象
            await meta_session.refresh(orm_model)
            print(orm_model.description)

    # asyncio.run(test_meta_session())

