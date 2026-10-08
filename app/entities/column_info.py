from dataclasses import dataclass
from typing import Any

@dataclass
class ColumnInfo:
  id: str # 字段ID构成=表ID.字段名称
  name: str # 字段名称
  type: str # 数据类型
  role: str # 字段角色
  examples: list[Any] # 实例值
  description: str  # 字段描述
  alias: list[str]  # 字段别名
  table_id: str # 所属的表ID