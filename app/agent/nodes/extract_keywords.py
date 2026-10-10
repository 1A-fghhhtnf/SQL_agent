import jieba.analyse
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def extract_keywords(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """抽取关键词节点：对用户问题进行分词得到关键词列表 用于后续的召回节点使用"""
    writer = get_stream_writer()
    try:
        writer({"type": "progress", "step": "抽取关键词", "status": "running"})
        #1.从状态获取用户提问
        query = state["query"]
        #2.采用jieba进行分词
        allow_pos = (
            "n",  # 名词: 数据、服务器、表格
            "nr",  # 人名: 张三、李四
            "ns",  # 地名: 北京、上海
            "nt",  # 机构团体名: 政府、学校、某公司
            "nz",  # 其他专有名词: Unicode、哈希算法、诺贝尔奖
            "v",  # 动词: 运行、开发
            "vn",  # 名动词: 工作、研究
            "a",  # 形容词: 美丽、快速
            "an",  # 名形词: 难度、合法性、复杂度
            "eng",  # 英文
            "i",  # 成语
            "l",  # 常用固定短语
        )
        keywords:list[str] = jieba.analyse.extract_tags(query, allowPOS=allow_pos)
        #3.得到关键词列表=抽取后关键词+原问题
        keywords = list(set(keywords+[query]))
        #4.更新state
        writer({"type": "progress", "step": "抽取关键词", "status": "success"})
        return {"keywords": keywords}
    except Exception as e:
        writer({"type": "progress", "step": "抽取关键词", "status": "error"})
        raise e
