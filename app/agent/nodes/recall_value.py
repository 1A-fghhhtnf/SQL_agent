import asyncio

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.value_info import ValueInfo
from app.prompt.prompt_loader import load_prompt


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """召回字段取值 获取用户问题中可能用到字段取值列表 获取字段ID"""
    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "召回字段取值", "status": "running"})
        # TODO 业务逻辑
        # 1.调用llm扩关键词 获取用户问题中可能用到字段取值列表
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_value_recall"), input_variables=["query"])
        chain = prompt | llm | JsonOutputParser()
        result = await chain.ainvoke({"query": state["query"]})
        keywords = list(set(state["keywords"]+result))

        # 2.执行ES全文检索
        retrieved_value_dict:dict[str, ValueInfo] = {}
        #2.1 从runtime上下文获取es持久层对象
        value_info_repository = runtime.context["value_info_repository"]
        #2.2 遍历关键词列表 执行ES全文检索
        for keyword in keywords:
            value_infos:list[ValueInfo] = await value_info_repository.search(keyword)
            # 3.解析结果
            for value_info in value_infos:
                if value_info.id not in retrieved_value_dict:
                    retrieved_value_dict[value_info.id] = value_info
        writer({"type": "progress", "step": "召回字段取值", "status": "success"})
        logger.info("召回字段取值成功:{}", list(retrieved_value_dict.values()))
        # 4.更新state
        return {"retrieved_values": list(retrieved_value_dict.values())}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "召回字段取值", "status": "error"})
        raise e
