from dataclasses import dataclass

@dataclass
class MetricInfo:
  id: str # 指标ID/名称
  name: str # 指标ID/名称
  description: str
  relevant_columns: list[str] # 关联字段ID列表
  alias: list[str] # 字段别名