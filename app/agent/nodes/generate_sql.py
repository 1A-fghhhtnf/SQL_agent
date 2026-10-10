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


async def generate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "生成SQL", "status": "running"})
        #1.从state获取五项数据 包含：①用户问题 ②表格列表 ③指标列表 ④日期信息  ⑤数据库信息
        query = state["query"]
        table_infos:list[TableInfoState] = state["table_infos"]
        state_metric_infos:list[MetricInfoState] = state["metric_infos"]
        date_info:DateInfoState = state["date_info"]
        db_info:DBInfoState = state["db_info"]
        #2.调用llm生成是纯文本SQL 解析器使用字符串
        prompt = PromptTemplate(template=load_prompt('generate_sql'), input_variables=["query", "table_infos", "metric_infos", "date_info", "db_info"])
        chain  = prompt | llm | StrOutputParser()
        sql = await chain.ainvoke({
            "query": query,
            "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            "metric_infos": yaml.dump(state_metric_infos, allow_unicode=True, sort_keys=False),
            "date_info":yaml.dump(date_info, allow_unicode=True, sort_keys=False),
            "db_info":yaml.dump(db_info, allow_unicode=True, sort_keys=False),
        })
        writer({"type": "progress", "step": "生成SQL", "status": "success"})
        logger.info("生成的SQL：{}", sql)
        #3.更新State状态
        return {"sql": sql}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "生成SQL", "status": "error"})
        raise e
