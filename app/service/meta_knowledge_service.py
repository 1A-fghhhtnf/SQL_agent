import uuid
from pathlib import Path
from typing import Any

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig, TableConfig, MetricConfig
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo
from app.repositories.es.value_es_repository import ValueInfoRepository
from app.repositories.mysql.dw_mysql_repository import DwMySQLRepository
from app.repositories.mysql.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:

    def __init__(self, metric_qdrant_repository:MetricQdrantRepository,value_info_repository: ValueInfoRepository, column_qdrant_repository: ColumnQdrantRepository,
                 embedding_client: HuggingFaceEndpointEmbeddings, dw_mysql_repository: DwMySQLRepository,
                 meta_mysql_repository: MetaMySQLRepository):
        """通过业务层初始化方法注入共计6个对象"""
        self.dw_mysql_repository = dw_mysql_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.value_info_repository = value_info_repository
        self.metric_qdrant_repository = metric_qdrant_repository

    async def build(self, meta_config_path: Path):
        logger.info("业务层被调用：{}", meta_config_path)
        # 1.通过OmegaConf读取yaml文件封装到dataclass对象中
        # 1.1 读取yaml文件得到OmegaConf对象 yaml中内容
        content = OmegaConf.load(meta_config_path)
        # 1.2 读取dataclass数据类得到OmegaConf对象 对应yaml结构
        structured = OmegaConf.structured(MetaConfig)
        # 1.3 将内容跟结构合并转为dataclass对象
        meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(structured, content))

        # 2. 处理表格信息
        if meta_config.tables:
            # 2.1 将表以及表中包含字段信息存入元数据库meta库
            column_infos: list[ColumnInfo] = await self._save_table_infos_to_meta_db(meta_config.tables)
            logger.info("将表/字段信息存入meta数据库成功")

            # 2.2 将字段信息建立向量索引 字段名称、描述、别名 存入Qdrant向量库
            await self._save_column_info_to_qdrant(column_infos)
            logger.info("为字段信息建立向量索引成功")

            # 2.3 将字段取值建立全文索引 字段所有取值 存入Elasticsearch全文库
            await self._save_column_info_to_es(meta_config.tables, column_infos)
            logger.info("为字段取值建立全文索引成功")

        # 3. 处理指标信息
        if meta_config.metrics:
            # 3.1 将指标信息存入元数据库meta库 返回 指标信息列表
            metric_infos:list[MetricInfo] = await self._save_metric_info_to_meta_db(meta_config.metrics)
            logger.info("将指标信息存入meta数据库成功")
            # 3.2 为指标建立向量索引 指标名称、描述、别名 存入Qdrant向量库
            await self._save_metric_info_to_qdrant(metric_infos)
            logger.info("为指标信息建立向量索引成功")

    async def _save_table_infos_to_meta_db(self, tables: list[TableConfig]) -> list[ColumnInfo]:
        """准备持久层保存表信息、字段信息 业务模型 列表  持久层调用转换器 转为ORM模型"""
        # 1. 声明列表存放表信息、字段信息
        table_infos: list[TableInfo] = []
        column_infos: list[ColumnInfo] = []
        # 2. 处理表信息
        # 2.1. 遍历表信息配置 列表
        for table_config in tables:
            table_info = TableInfo(
                id=table_config.name,
                name=table_config.name,
                role=table_config.role,
                description=table_config.description,
            )
            table_infos.append(table_info)
            # 3.  处理字段信息
            # 3.1 调用数仓持久层根据表ID查询该表字段数据类型 返回字典：{字段名称:数据类型}
            column_type_dict: dict[str, str] = await self.dw_mysql_repository.get_column_type_by_table_id(table_info.id)
            for column_config in table_config.columns:
                # 3.2 调用数仓持久层查询指定字段个别示例取值
                examples: list[str] = await self.dw_mysql_repository.get_column_values(table_info.id,
                                                                                       column_config.name)
                column_info = ColumnInfo(
                    id=f"{table_info.id}.{column_config.name}",
                    name=column_config.name,
                    role=column_config.role,
                    description=column_config.description,
                    alias=column_config.alias,
                    table_id=table_info.id,
                    type=column_type_dict[column_config.name],
                    examples=examples
                )
                column_infos.append(column_info)
        # 4. 调用meta库持久层 保存表跟字段信息
        await self.meta_mysql_repository.save_table_infos(table_infos)
        await self.meta_mysql_repository.save_column_infos(column_infos)
        # 5. 返回字段信息列表 用于构建向量+全文索引
        return column_infos

    async def _save_column_info_to_qdrant(self, column_infos: list[ColumnInfo]):
        """准备qdrant持久层向量点结构需要的数据，调用持久层保存向量点"""
        # 1.确保字典向量集合存在
        await self.column_qdrant_repository.ensure_collection()

        # 2.构建向量点三项信息：ID、向量、元数据（字段信息）
        # 2.1 声明存放向量点列表
        points: list[dict] = []
        # 2.2 遍历字段列表 构建向量点字典：id,待转向量文本,字段信息
        for column_info in column_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.name,
                "payload": column_info
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.description,
                "payload": column_info
            })
            for alias in column_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alias,
                    "payload": column_info
                })
        # 2.3 分批次对所有文本进行向量化
        embeddeds: list[list[float]] = []
        embedding_texts = [point["embedding_text"] for point in points]
        batch_size = 10
        for i in range(0, len(embedding_texts), batch_size):
            batch_embedding_text = embedding_texts[i:i + batch_size]
            batch_embedded = await self.embedding_client.aembed_documents(batch_embedding_text)
            embeddeds.extend(batch_embedded)

        # 3.调用qdrant持久层批量新增向量点
        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.column_qdrant_repository.upsert(ids, payloads, embeddeds)

    async def _save_column_info_to_es(self, table_configs: list[TableConfig], column_infos: list[ColumnInfo]):
        """
            准备ES持久层需要数据
        :param table_configs: 得到字段是否需要同步标识 sync
        :param column_infos:  所有字段列表
        :return:
        """
        # 1.创建索引库手动指定映射 确保索引库存在
        await self.value_info_repository.ensure_index()

        # 2.获取字段取值信息
        value_infos:list[ValueInfo] = []
        # 2.1 从yaml中获取需要建立全文索引字段名称列表
        need_sync_to_es:list[str] = [column.name for table in table_configs for column in table.columns if column.sync is True]

        # 2.2 遍历字段信息列表 只要该字段需要建立全文索引，构建ES文档对象：ValueInfo
        for column_info in column_infos:
            column_name = column_info.name
            if column_name in need_sync_to_es:
                #2.2.1 根据表ID+字段名称获取该字段所有取值
                column_values:list[str]= await self.dw_mysql_repository.get_column_values(column_info.table_id, column_name, limit=1000000)
                #2.2.2 构建ES文档对象ValueInfo
                for column_value in column_values:
                    value_info = ValueInfo(
                        id=f"{column_info.id}.{column_value}",
                        value=column_value,
                        column_id=column_info.id
                    )
                    value_infos.append(value_info)
        # 3.调用es持久层批量新增文档到ES索引库
        await self.value_info_repository.upsert(value_infos)

    async def _save_metric_info_to_meta_db(self, metrics:list[MetricConfig]) ->list[MetricInfo]:
        """准备持久层需要指标列表、字段指标关系列表，调用meta持久层保存指标信息到meta数据库"""
        #1.声明列表存放指标信息、字段指标关系信息
        metric_infos: list[MetricInfo] = []
        column_metric_infos: list[ColumnMetric] = []

        #2.遍历指标信息列表 处理指标、处理字段指标关系
        for metric_config in metrics:
            metric_info = MetricInfo(
                id=metric_config.name,
                name=metric_config.name,
                description=metric_config.description,
                relevant_columns=metric_config.relevant_columns,
                alias=metric_config.alias,
            )
            metric_infos.append(metric_info)
            for relevant_column in metric_config.relevant_columns:
                column_metric_info = ColumnMetric(
                    column_id=relevant_column,
                    metric_id=metric_info.id
                )
                column_metric_infos.append(column_metric_info)

        #3.调用持久层保存指标信息、字段指标关系信息
        await self.meta_mysql_repository.save_metric_infos(metric_infos)
        await self.meta_mysql_repository.save_column_metric_infos(column_metric_infos)
        #4.返回指标信息列表
        return metric_infos

    async def _save_metric_info_to_qdrant(self, metric_infos:list[MetricInfo]):
        """准备qdrant持久层向量点结构需要的数据，调用持久层保存向量点"""
        #1.确保指标向量集合存在
        await self.metric_qdrant_repository.ensure_collection()

        #2.构建向量点三项信息：ID、向量、元数据（字段信息）
        #2.1 声明列表存放向量点字典
        points:list[dict[str, Any]] = []
        #2.2 遍历指标列表，将指标名称、别名、描述构建字典
        for metric_info in metric_infos:
            points.append({
                "id":uuid.uuid4(),
                "payload":metric_info,
                "embedding_text":metric_info.name
            })
            points.append({
                "id": uuid.uuid4(),
                "payload": metric_info,
                "embedding_text": metric_info.description
            })
            for alias in metric_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "payload": metric_info,
                    "embedding_text": alias
                })
        #2.3 采用分批次对所有文本进行向量化
        embeddeds = []
        batch_size = 10
        embedding_texts = [point["embedding_text"] for point in points]
        for i in range(0,len(embedding_texts), batch_size):
            batch_embedding_text = embedding_texts[i:i + batch_size]
            batch_embedded = await self.embedding_client.aembed_documents(batch_embedding_text)
            embeddeds.extend(batch_embedded)

        #3.调用qdrant持久层批量新增向量点
        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.metric_qdrant_repository.upsert(ids, payloads, embeddeds)
