from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def generate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "生成SQL", "status": "running"})
        #TODO 业务逻辑
        writer({"type": "progress", "step": "生成SQL", "status": "success"})
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "生成SQL", "status": "error"})
        raise e
