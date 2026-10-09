from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def correct_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "修复SQL", "status": "running"})
        #TODO 业务逻辑
        writer({"type": "progress", "step": "修复SQL", "status": "success"})
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "修复SQL", "status": "error"})
        raise e
