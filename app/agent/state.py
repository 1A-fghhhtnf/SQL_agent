from typing import TypedDict

from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo


class DataAgentState(TypedDict):
    """状态"""
    query: str  # 用户提出问题
    keywords:list[str] # 抽取关键词节点产生结果
    retrieved_columns: list[ColumnInfo]  # 召回的字段节点产生结果
    retrieved_metrics: list[MetricInfo] # 召回指标节点产生的结果
    retrieved_values: list[ValueInfo] # 召回字段取值节点产生的结果
    error:str # 校验SQL节点用于产生错误信息
