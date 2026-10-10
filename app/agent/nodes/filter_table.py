import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, TableInfoState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """过滤表格:将不需要的表格(包含字段)过滤掉"""
    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "过滤表格", "status": "running"})
        #1.获取state中候选表格、用户问题
        table_infos:list[TableInfoState] = state["table_infos"]
        query = state["query"]
        #2.调用llm返回需要的表跟字段
        prompt = PromptTemplate(template=load_prompt('filter_table_info'),input_variables=["query","table_infos"])
        chain = prompt|llm|JsonOutputParser()
        # {
        #     "需要表名1": ["需要字段1", "需要字段2", "..."],
        #     "需要表名2": ["需要字段1", "需要字段2", "..."]
        # }
        result = await chain.ainvoke({
            "query": query,
            "table_infos": yaml.dump(table_infos, default_flow_style=False, sort_keys=False)
        })
        #3.遍历候选表格，将不需要的表过滤掉，将表中不需要字段过滤掉
        for table_info in table_infos[:]:
            if table_info["name"] not in result:
                # 表不需要
                table_infos.remove(table_info)
            else:
                # 表需要，进一步判断字段是否需要
                columns = table_info["columns"]
                for column in columns[:]:
                    if column["name"] not in result[table_info["name"]]:
                        columns.remove(column)
        writer({"type": "progress", "step": "过滤表格", "status": "success"})
        logger.info("过滤表格成功:{}", table_infos)
        #4.更新state
        return {"table_infos": table_infos}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "过滤表格", "status": "error"})
        raise e
