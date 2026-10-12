from functools import lru_cache
from typing import Union, Annotated

import anyio
from async_lru import alru_cache
from fastapi import APIRouter, Query, Path
from fastapi.params import Depends
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

# 1.创建路由对象
hello_router = APIRouter(tags=["用于测试"])


# 2.提供路由接口
@hello_router.get("/hello")
async def hello():
    return {"message": "Hello World"}


# 获取查询参数 例如：/api/test?name=zhangsan&age=18
@hello_router.get("/api/test")
async def get_query_param(name: str = Query(min_length=2, max_length=10, description="请输入用户名"),
                          age: int = Query(gt=0, lt=150, description="请输入年龄")):
    return {"data": {"name": name, "age": age}}


# 获取路径参数  例如：/api/test1/{name}/{age}
@hello_router.get("/api/test1/{name}/{age}")
async def get_path_param(name: str = Path(min_length=2, max_length=10, description="请输入用户名"),
                         age: int = Path(gt=0, lt=150, description="请输入年龄")):
    return {"data": {"name": name, "age": age}}


async def fake_video_streamer():
    for i in range(10):
        yield f"data: stage:{i} \n\n"
        await anyio.sleep(1)


@hello_router.get("/api/streaming")
async def get_streaming():
    return StreamingResponse(fake_video_streamer(), media_type="text/event-stream;charset=utf-8")


# 获取json请求体参数
class User(BaseModel):
    name: str
    age: int
    email: str | None = Field(description="请输入邮箱")
    phone: Union[str, None] = None


@hello_router.post("/api/test2")
async def get_body_param(user: User):
    return user

#@lru_cache只能用在同步函数中 输入参数及结果进行缓存，从而提高效率。当缓存达到预设的上限时，它会自动淘汰最久未使用的数据。
#@alru_cache 异步环境中实现高效的缓存机制，从而显著提升程序性能
@alru_cache
async def my_dict() -> dict[str, str]:
    print("my_dict被调用")
    """返回一个字典作为依赖项"""
    return {"a": "1", "b": "2"}


@hello_router.get("/api/dep1")
async def get_dependency1(d1: Annotated[dict, Depends(my_dict)]):
    return d1


@hello_router.get("/api/dep2")
async def get_dependency2(d2: dict = Depends(my_dict)):
    return d2


if __name__ == '__main__':
    def test():
        yield 1
        yield 2
        yield 3


    # 创建生成器
    g = test()

    # 每次调用，只走到下一个 yield，然后停住
    print(next(g))  # 1
    print(next(g))  # 2
    print(next(g))  # 3
