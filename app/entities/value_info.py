from dataclasses import dataclass

@dataclass
class ValueInfo:
  """字段取值构建文档对象"""
  id: str #字段ID.字段取值 类型：keyword
  value: str #字段取值    类型：text + ik_max_word
  column_id: str #字段ID 类型：keyword