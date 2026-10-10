from datetime import datetime

from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, DateInfoState, DBInfoState
from app.core.log import logger


async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """添加额外上下文：当前时间解决问题中相对时间提问、数仓数据库信息"""
    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "添加额外上下文", "status": "running"})
        #1.获取时间
        today = datetime.today()
        # 日期
        date = today.strftime("%Y-%m-%d")
        # 星期
        weekday = today.strftime("%A")
        # 季度
        quarter = f"Q{(today.month - 1) // 3 + 1}"
        date_info = DateInfoState(
            date=date,
            weekday=weekday,
            quarter=quarter
        )
        logger.info("额外上下文日期信息：{}", date_info)
        #2.获取数仓dw数据库信息
        dw_mysql_repository = runtime.context["dw_mysql_repository"]
        db_info_dict:dict[str, str] = await dw_mysql_repository.get_db_info()
        db_info = DBInfoState(
            dialect=db_info_dict["dialect"],
            version=db_info_dict["version"]
        )
        writer({"type": "progress", "step": "添加额外上下文", "status": "success"})
        logger.info("额外上下文数据库信息：{}", db_info)
        #3.更新state
        return {"date_info": date_info, "db_info": db_info}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "添加额外上下文", "status": "error"})
        raise e
