from pydantic import BaseModel, Field


class QuerySchema(BaseModel):
    query:str = Field(description="用户问题", min_length=5, max_length=100)