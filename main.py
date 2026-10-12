import time
import uuid
from urllib.request import Request

import uvicorn
from fastapi import FastAPI

from app.api.routers.hello_router import hello_router
from app.api.routers.query_router import query_router
from app.core.context import request_id_ctx_var
from app.core.lifespan import lifespan

# 1.创建fastAPI实例
app = FastAPI(lifespan=lifespan)

# 2.引入自定义路由
app.include_router(hello_router)
app.include_router(query_router)

#3.添加中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
     为每次请求新增处理逻辑
    :param request: 请求对象
    :param call_next: 调用路由处理函数
    :return: 响应对象
    """
    start_time = time.perf_counter()
    # 为本次请求服务端产生的协程对象设置请求ID
    request_id_ctx_var.set(str(uuid.uuid4()))
    # 调用路由处理函数->路由层->业务层->数据层
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    # 将接口耗时采用响应头发方式返回
    response.headers["X-Process-Time"] = str(process_time)
    return response


if __name__ == '__main__':
    """
    命令行启动方式：1.fastapi dev 2.uv run python -m main
    PyCharm工具新建运行配置：注意：如果是断点调试 去掉：--reload参数
    """
    uvicorn.run(app="main:app", reload=True)
