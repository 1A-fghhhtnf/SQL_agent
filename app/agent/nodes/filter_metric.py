import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, MetricInfoState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """过滤指标:将不需要的指标过滤掉"""
    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "过滤指标", "status": "running"})
        #1.获取state候选指标列表、用户问题
        metric_infos:list[MetricInfoState] = state["metric_infos"]
        query = state["query"]
        #2.调用llm返回需要：指标列表 包含指标名称
        prompt = PromptTemplate(template=load_prompt('filter_metric_info'), input_variables=["query", "metric_infos"])
        chain = prompt | llm | JsonOutputParser()
        # [
        #   "需要指标1",
        #   "需要指标2"
        # ]
        result = await chain.ainvoke({
            "query":query,
            "metric_infos":yaml.dump(metric_infos, allow_unicode=True, sort_keys=False)
        })
        #3.遍历候选指标，将不需要的指标过滤掉 循环中不能删除元素可能造成漏删 解决办法：通过[:]切片表达式复制一份列表 原理：遍历是副本，删除是原列表
        for metric_info in metric_infos[:]:
            if metric_info["name"] not in result:
                metric_infos.remove(metric_info)
        writer({"type": "progress", "step": "过滤指标", "status": "success"})
        logger.info("过滤指标成功:{}", metric_infos)
        #4.更新state中指标信息
        return {"metric_infos": metric_infos}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "过滤指标", "status": "error"})
        raise e
