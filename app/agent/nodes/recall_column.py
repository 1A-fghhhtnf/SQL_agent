from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.prompt.prompt_loader import load_prompt


async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """
        回答问题所需要的字段列表
    :param state: 状态
    :param runtime: 运行时对象
    :return:
    """
    writer = runtime.stream_writer
    try:
        writer({"type": "progress", "step": "召回字段", "status": "running"})
        # 1.对用户问题调用llm进行扩充回答问题所需要的（中文语义）字段列表 得到关键词列表
        keywords = state["keywords"]
        # 1.1 创建提示词对象
        prompt = PromptTemplate(template=load_prompt('extend_keywords_for_column_recall'), input_variables=["query"])
        # 1.2 创建langchain链
        chain = prompt | llm | JsonOutputParser()
        # 1.3 执行异步调用 获取到 字段列表  关键词列表=jieba分词后结果+字段列表
        result:list[str] = await chain.ainvoke({"query": state["query"]})
        keywords = list(set(result+keywords))

        # 2.查询qdrant数据库字段信息集合
        #2.1 从runtime的上下文中获取embedding客户端、字段信息qdrant持久层
        embedding_client = runtime.context["embedding_client"]
        column_qdrant_repositor = runtime.context["column_qdrant_repository"]
        #2.2 遍历关键词列表，对每个关键词转为向量后进行语义相似度检索
        retrieved_column_info_dict:dict[str, ColumnInfo] = {} #key:字段ID  value:字段信息对象
        for keyword in keywords:
            vector:list[float] = await embedding_client.aembed_query(keyword)
            column_infos:list[ColumnInfo] = await column_qdrant_repositor.search(vector)
            #2.3 解析获取结果
            # 避免存在重复的字段信息，进行去重
            for column_info in column_infos:
                if column_info.id not in retrieved_column_info_dict:
                    retrieved_column_info_dict[column_info.id] = column_info
        writer({"type": "progress", "step": "召回字段", "status": "success"})
        logger.info("召回字段成功：{}", list(retrieved_column_info_dict.keys()))
        # 3.更新state状态
        return {"retrieved_columns": list(retrieved_column_info_dict.values())}
    except Exception as e:
        writer({"type": "progress", "step": "召回字段", "status": "error"})
        logger.error(e)
        raise e
