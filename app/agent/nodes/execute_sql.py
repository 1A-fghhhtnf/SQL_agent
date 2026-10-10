from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def execute_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """执行SQL：执行数仓查询，将查询结果返回"""
    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "执行SQL", "status": "running"})
        #1.从state获取业务SQL‘
        sql = state["sql"]

        #2.执行数仓查询（dw库）
        dw_mysql_repository = runtime.context["dw_mysql_repository"]
        data = await dw_mysql_repository.execute_sql(sql)
        writer({"type": "progress", "step": "执行SQL", "status": "success"})
        logger.info("SQL执行结果：{}", data)
        #3.将查询结果写回
        writer({"type": "result", "data":data})
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "执行SQL", "status": "error"})
        raise e
