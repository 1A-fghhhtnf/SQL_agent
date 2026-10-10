import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, TableInfoState, MetricInfoState, DateInfoState, DBInfoState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def correct_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """修正有问题SQL"""
    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "修复SQL", "status": "running"})
        #1.判断状态中修复次数是否已经达到3次 如果是则抛出异常 终止流程
        modify_count = state.get("modify_count", 1)
        if modify_count >= 3:
            raise Exception("SQL修复次数达到3次，终止流程")
        #2.调用llm SQL修复
        query = state["query"]
        table_infos: list[TableInfoState] = state["table_infos"]
        state_metric_infos: list[MetricInfoState] = state["metric_infos"]
        date_info: DateInfoState = state["date_info"]
        db_info: DBInfoState = state["db_info"]
        error = state["error"]
        sql = state["sql"]
        prompt = PromptTemplate(template=load_prompt('correct_sql'), input_variables=["sql", "error","query", "table_infos", "metric_infos", "date_info", "db_info"])
        chain = prompt | llm | StrOutputParser()
        new_sql = await chain.ainvoke({
            "query": query,
            "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            "metric_infos": yaml.dump(state_metric_infos, allow_unicode=True, sort_keys=False),
            "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False),
            "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False),
            "error":error,
            "sql":sql
        })
        writer({"type": "progress", "step": "修复SQL", "status": "success"})
        logger.info(f"修复后的SQL: {new_sql}")
        #3.更新state状态中SQL
        return {"sql":new_sql, "modify_count": modify_count + 1}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "修复SQL", "status": "error"})
        raise e
