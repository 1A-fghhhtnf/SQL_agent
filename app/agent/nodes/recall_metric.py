import asyncio

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.metric_info import MetricInfo
from app.prompt.prompt_loader import load_prompt


async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "召回指标", "status": "running"})
        # 1.调用llm扩充关键词 获取到回答问题可能需要指标列表 关键词列表=分词后结果+llm指标列表
        # 1.1 创建提示词对象
        prompt = PromptTemplate(template=load_prompt('extend_keywords_for_metric_recall'), input_variables=["query"])

        # 1.2 构建langchain链
        chain = prompt | llm | JsonOutputParser()
        # 1.3 执行异步调用
        result: list[str] = await chain.ainvoke({"query": state["query"]})
        keywords = list(set(state["keywords"] + result))
        # 2.遍历关键词列表，对每个关键词执行语义相似度检索
        retrieved_metrics_dict: dict[str, MetricInfo] = {}

        # 2.1 从runtime上下文获取embedding客户端、指标集合持久层对象
        embedding_client = runtime.context["embedding_client"]
        metric_qdrant_repositor = runtime.context["metric_qdrant_repository"]
        # 2.2 对关键词列表转向量 执行语义相似度检索
        vectors:list[list[float]] = await embedding_client.aembed_documents(keywords)
        metric_infos: list[MetricInfo] = await metric_qdrant_repositor.search_batch(vectors)
        # 3.解析结果，结果注意去重
        for metric_info in metric_infos:
            if metric_info.id not in retrieved_metrics_dict:
                retrieved_metrics_dict[metric_info.id] = metric_info
        ############ 循环每个关键词执行语义相似度检索-begin##########
        # for keyword in keywords:
        #     vector: list[float] = await embedding_client.aembed_query(keyword)
        #     metric_infos: list[MetricInfo] = await metric_qdrant_repositor.search(vector)
        #     # 3.解析结果，结果注意去重
        #     for metric_info in metric_infos:
        #         if metric_info.id not in retrieved_metrics_dict:
        #             retrieved_metrics_dict[metric_info.id] = metric_info
        ############ 循环每个关键词执行语义相似度检索-end##########
        writer({"type": "progress", "step": "召回指标", "status": "success"})
        logger.info("召回指标成功：{}", list(retrieved_metrics_dict.keys()))
        # 4.更新state状态
        return {"retrieved_metrics": list(retrieved_metrics_dict.values())}
    except Exception as e:
        logger.error(str(e))
        writer({"type": "progress", "step": "召回指标", "status": "error"})
        raise e
