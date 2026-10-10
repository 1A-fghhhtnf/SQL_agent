from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "校验SQL", "status": "running"})
        #1.获取到生成的SQL
        sql = state["sql"]
        #2.生成SQL只能是select查询语句
        if not sql:
            return {"error": "SQL为空"}
        if not sql.lower().startswith("select"):
            return {"error": "生成的SQL只能是select查询语句"}
        #3.调用dw持久层通过执行计划验证SQL合法性
        dw_mysql_repository = runtime.context["dw_mysql_repository"]
        await dw_mysql_repository.validate_sql(sql)
        writer({"type": "progress", "step": "校验SQL", "status": "success"})
        return {"error": None}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "校验SQL", "status": "error"})
        return {"error": str(e)}
