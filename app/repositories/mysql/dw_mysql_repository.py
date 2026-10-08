from sqlalchemy import text, Result
from sqlalchemy.ext.asyncio import AsyncSession


class DwMySQLRepository:
    """操作数据仓库的mysql持久层"""

    def __init__(self, session: AsyncSession):
        """持久层框架关键获取到Session就可以操作数据库"""
        self.session = session

    async def get_column_type_by_table_id(self, table_id: str) -> dict[str, str]:
        # 1.准备自定义SQL
        sql = f"show columns from {table_id}"
        # 2.执行自定义SQL 结果：多行多列
        result: Result = await self.session.execute(text(sql))

        # 3.解析查询结果，通过row对象获取字段名称跟数据类型，封装字典返回
        fetchall = result.fetchall()
        return {row.Field:row.Type  for row in fetchall}

    async def get_column_values(self, table_id:str, column_name:str, limit:int=3) ->list[str]:
        """查询指定表指定字段取值"""
        sql = f"SELECT DISTINCT {column_name} from {table_id} limit {limit}"
        result: Result = await self.session.execute(text(sql))
        #执行自定义SQL解析单列多行结果
        return result.scalars().fetchall()
