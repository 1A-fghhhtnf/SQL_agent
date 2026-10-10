from typing import TypedDict

import yaml

from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo

class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]


class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]

class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]

class DateInfoState(TypedDict):
    date: str
    weekday: str
    quarter: str


class DBInfoState(TypedDict):
    dialect: str
    version: str

class DataAgentState(TypedDict):
    """状态"""
    query: str  # 用户提出问题
    keywords:list[str] # 抽取关键词节点产生结果
    retrieved_columns: list[ColumnInfo]  # 召回的字段节点产生结果
    retrieved_metrics: list[MetricInfo] # 召回指标节点产生的结果
    retrieved_values: list[ValueInfo] # 召回字段取值节点产生的结果

    table_infos: list[TableInfoState]  # 合并节点产生结果
    metric_infos: list[MetricInfoState]  # 合并节点产生结果

    date_info: DateInfoState  # 增加额外上下文节点产生结果日期信息
    db_info: DBInfoState  # 增加额外上下文节点产生结果数据库信息

    sql:str # 生成SQL节点用于产生SQL结果

    error:str # 校验SQL节点用于产生错误信息

    modify_count:int #记录修复SQL次数