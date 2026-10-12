from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from starlette.responses import StreamingResponse

from app.api.dependencies import get_query_service
from app.api.schemas import QuerySchema
from app.service.query_service import QueryService

query_router = APIRouter(tags=["问数提问"])


#1.路由层 负责处理请求 接收参数 响应结果
@query_router.post("/api/query")
async def query(query_schema:QuerySchema, query_service:Annotated[QueryService, Depends(get_query_service)]):
    # 流式响应业务层chunk块内容
    return StreamingResponse(query_service.query(query_schema.query), media_type="text/event-stream;charset=utf-8")