"""操作数据仓库的mysql持久层"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.mappers.column_info_mapper import ColumnInfoMapper
from app.mappers.column_metric_mapper import ColumnMetricMapper
from app.mappers.metric_info_mapper import MetricInfoMapper
from app.mappers.table_info_mapper import TableInfoMapper


class MetaMySQLRepository:
    """操作元数据的mysql持久层"""


    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_table_infos(self, table_infos:list[TableInfo]):
        #1.通过列表推导式 将TableInfo转为TableInfoMySQL ORM模型
        models = [TableInfoMapper.to_model(table_info) for table_info in table_infos]
        #2.调用session批量新增方法即可
        self.session.add_all(models)

    async def save_column_infos(self, column_infos:list[ColumnInfo]):
        models = [ColumnInfoMapper.to_model(column_info) for column_info in column_infos]
        self.session.add_all(models)

    async def save_metric_infos(self, metric_infos:list[MetricInfo]):
        models = [MetricInfoMapper.to_model(metric_info) for metric_info in metric_infos]
        self.session.add_all(models)

    async def save_column_metric_infos(self, column_metric_infos:list[ColumnMetric]):
        models = [ColumnMetricMapper.to_model(column_metric_info) for column_metric_info in column_metric_infos]
        self.session.add_all(models)