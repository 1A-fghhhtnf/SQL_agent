from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo
from app.entities.table_info import TableInfo
from app.repositories.mysql.meta_mysql_repository import MetaMySQLRepository
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, TableInfoState, ColumnInfoState, MetricInfoState
from app.core.log import logger

async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):

    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "合并召回信息", "status": "running"})
        #TODO 业务逻辑
        #1.以已召回字段列表为基础，将已召回指标中字段（可能需要根据字段ID查询meta库获取字段信息） 以及 已召回字段取值中字段合并到一起
        #1.1 处理已召回字段列表 得到字段id跟字段信息映射字典 方便去重
        retrieved_columns:list[ColumnInfo] = state["retrieved_columns"]
        retrieved_columns_dict:dict[str, ColumnInfo] = {column.id:column  for column in retrieved_columns}
        #1.2 处理已召回指标 将指标包含字段信息 加入到字典中
        meta_mysql_repository:MetaMySQLRepository = runtime.context["meta_mysql_repository"]
        retrieved_metrics:list[MetricInfo] = state["retrieved_metrics"]
        for retrieved_metric in retrieved_metrics:
            for column_id in retrieved_metric.relevant_columns:
                if column_id not in retrieved_columns_dict:
                    # 根据字段ID 查询meta库column_info表得到字段信息对象
                    column_info:ColumnInfo = await meta_mysql_repository.get_column_info_by_id(column_id)
                    retrieved_columns_dict[column_id] = column_info
        #1.3 处理已召回取值 将取值包含字段信息 加入到字典中 将取值加入到字段的examples中
        retrieved_values:list[ValueInfo] = state["retrieved_values"]
        for value_info in retrieved_values:
            column_id = value_info.column_id
            if column_id not in retrieved_columns_dict:
                column_info:ColumnInfo = await meta_mysql_repository.get_column_info_by_id(column_id)
                retrieved_columns_dict[column_id] = column_info
            if value_info.value not in retrieved_columns_dict[column_id].examples:
                retrieved_columns_dict[column_id].examples.append(value_info.value)

        #2.遍历所有字段列表，按table_id进行分组 得到table_id跟字段列表映射--字典
        table_id_columns_dict:dict[str, list[ColumnInfo]] = {}
        for column_info in retrieved_columns_dict.values():
            # 当前字段所属表名称
            table_id = column_info.table_id
            if table_id not in table_id_columns_dict:
                table_id_columns_dict[table_id] = []
            table_id_columns_dict[table_id].append(column_info)

        #3.根据table_id获取每张主外键字段，增加主外键字段信息 遍历key即可 表->字段列表
        for table_id in table_id_columns_dict.keys():
            #3.1 获取现有表包含字段ID列表
            existing_column_ids = [column.id for column in table_id_columns_dict[table_id]]
            #3.2 根据表ID查询主外键字段信息列表 查询meta库column_info表
            key_columns:list[ColumnInfo] = await meta_mysql_repository.get_key_columns(table_id)
            #3.3 如果主外键字段不存在现有字段列表中，则将主外键字段信息添加到表中字段列表中
            for key_column in key_columns:
                column_id = key_column.id
                if column_id not in existing_column_ids:
                    table_id_columns_dict[table_id].append(key_column)


        #4.封装state中表信息列表 更新state  提供给大语言模型 需要的表以及表下字段列表
        table_infos:list[TableInfoState] = []
        for table_id, column_infos in table_id_columns_dict.items():
            #4.1 根据表ID查询表信息
            table_info:TableInfo = await meta_mysql_repository.get_table_info_by_id(table_id)
            #4.2 构建表state对象
            table_info_state = TableInfoState(
                name=table_info.name,
                role=table_info.role,
                description=table_info.description,
                #4.3 处理表种包含字段列表
                columns = [ColumnInfoState(
                    name=column.name,
                    type=column.type,
                    role=column.role,
                    examples=column.examples,
                    description=column.description,
                    alias=column.alias
                ) for column in column_infos]
            )
            table_infos.append(table_info_state)
        logger.info("合并召回信息节点: {}", table_infos)
        #5.封装state指标信息列表 更新state  提供给大语言模型需要的指标列表
        metric_infos: list[MetricInfoState] = []

        for metric_info in retrieved_metrics:
            metric_infos.append(
                MetricInfoState(
                    name=metric_info.name,
                    alias=metric_info.alias,
                    description=metric_info.description,
                    relevant_columns=metric_info.relevant_columns)
            )
        logger.info("合并召回信息节点: {}", metric_infos)
        writer({"type": "progress", "step": "合并召回信息", "status": "success"})
        #6.更新State
        return {"table_infos": table_infos, "metric_infos": metric_infos}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "合并召回信息", "status": "error"})
        raise e
