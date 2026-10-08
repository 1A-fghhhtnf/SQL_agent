from dataclasses import dataclass

@dataclass
class TableInfo:
    """dataclass数据类用于业务层"""

    id: str # 表ID/名称
    name: str # 表ID/名称
    role: str # 表角色 ： 维度表 事实表
    description: str # 表描述