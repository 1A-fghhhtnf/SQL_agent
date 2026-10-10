"""操作数据仓库的mysql持久层"""
from app.models.column_info_mysql import ColumnInfoMySQL
from app.models.table_info_mysql import TableInfoMySQL
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.mappers.column_info_mapper import ColumnInfoMapper
from app.mappers.column_metric_mapper import ColumnMetricMapper
from app.mappers.metric_info_mapper import MetricInfoMapper
from app.mappers.table_info_mapper import TableInfoMapper
from sqlalchemy import select


class MetaMySQLRepository:
    """操作元数据的mysql持久层"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_table_infos(self, table_infos: list[TableInfo]):
        # 1.通过列表推导式 将TableInfo转为TableInfoMySQL ORM模型
        models = [TableInfoMapper.to_model(table_info) for table_info in table_infos]
        # 2.调用session批量新增方法即可
        self.session.add_all(models)

    async def save_column_infos(self, column_infos: list[ColumnInfo]):
        models = [ColumnInfoMapper.to_model(column_info) for column_info in column_infos]
        self.session.add_all(models)

    async def save_metric_infos(self, metric_infos: list[MetricInfo]):
        models = [MetricInfoMapper.to_model(metric_info) for metric_info in metric_infos]
        self.session.add_all(models)

    async def save_column_metric_infos(self, column_metric_infos: list[ColumnMetric]):
        models = [ColumnMetricMapper.to_model(column_metric_info) for column_metric_info in column_metric_infos]
        self.session.add_all(models)

    async def get_column_info_by_id(self, column_id: str) -> ColumnInfo:
        """
            根据id获取字段信息
        :param id: 主键
        :return:
        """
        column_info_mysql: ColumnInfoMySQL|None = await self.session.get(ColumnInfoMySQL, column_id)
        return ColumnInfoMapper.to_entity(column_info_mysql)

    async def get_key_columns(self, table_id: str) -> list[ColumnInfo]:
        """
            根据表ID获取主外键字段信息列表
        :param table_id: 表ID
        :return: 主外键字段信息列表
        """
        stmt = select(ColumnInfoMySQL).where(ColumnInfoMySQL.table_id == table_id,
                                             ColumnInfoMySQL.role.in_(['primary_key', 'foreign_key']))
        # scalars()方法返回一个标量结果集 面向ORM模型 将结果中一条记录封装为“标量”
        column_info_mysqls: list[ColumnInfoMySQL] = await self.session.scalars(stmt)
        return [ColumnInfoMapper.to_entity(column_info_mysql) for column_info_mysql in column_info_mysqls]

    async def get_table_info_by_id(self, table_id: str) -> TableInfo|None:
        """
        根据表ID查询表信息
        :param table_id:
        :return:
        """
        table_info_mysql: TableInfoMySQL|None = await self.session.get(TableInfoMySQL, table_id)
        return TableInfoMapper.to_entity(table_info_mysql)
