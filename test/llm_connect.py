"""DeepSeek 连接连通性测试。

运行方式（在项目根目录 D:\\A_Py_Java\\pyFile\\data_agent 下执行）：
    ./.venv/Scripts/python.exe test/llm_connect.py

前置条件：
    环境变量 DEEPSEEK_API_KEY 已设置为真实 key。
    未设置时 app_config 会在导入阶段直接抛 InterpolationResolutionError。
"""
import os
import sys
from pathlib import Path

# 直接运行脚本时，Python 只把脚本所在目录(test/)加入 sys.path，
# 导致找不到项目根目录下的 app 包。这里手动把项目根目录补进去。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# 本测试只关心 DeepSeek 的连通性，关掉 LangSmith 追踪。
# 否则每次调用都会尝试上传 trace 到 LangSmith，失败后打印一堆 403 报错刷屏。
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from langchain.chat_models import init_chat_model

from app.conf.app_config import app_config

# 构建 langchain 模型对象（与参考项目 app/agent/llm.py 写法一致）
# 注意：ChatDeepSeek 的 base_url 参数名是 api_base，不是 base_url
llm = init_chat_model(
    model=app_config.llm.model_name,
    api_key=app_config.llm.api_key,
    api_base=app_config.llm.base_url,
    temperature=0,
)


def print_config():
    """打印当前生效的配置，便于排查连的是哪个地址、哪个模型。"""
    key = app_config.llm.api_key
    masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
    print("当前配置：")
    print(f"  model     = {app_config.llm.model_name}")
    print(f"  base_url  = {app_config.llm.base_url}")
    print(f"  api_key   = {masked}")
    print()


def test_invoke():
    """非流式调用：一次性拿到完整回复。"""
    print("[1/2] 非流式调用 invoke ...")
    result = llm.invoke("用一句话介绍你自己")
    print(f"  回复: {result.content}")
    print(f"  token 用量: {result.usage_metadata}")
    print()


def test_stream():
    """流式调用：逐块打印，验证流式链路。"""
    print("[2/2] 流式调用 stream ...")
    print("  回复: ", end="")
    for chunk in llm.stream("who are you?"):
        print(chunk.text, end="", flush=True)
    print("\n")


def diagnose(exc: Exception):
    """把常见异常翻译成人能看懂的排查建议。"""
    msg = str(exc)
    print(f"\n连接失败: {type(exc).__name__}")
    print(f"原始信息: {msg[:500]}\n")

    print("排查建议：")
    if "401" in msg or "Authentication" in msg or "invalid_api_key" in msg:
        print("  → key 无效。检查 DEEPSEEK_API_KEY 是否填了真实 key（sk- 开头）")
    elif "404" in msg or "model_not_found" in msg or "Model Not Exist" in msg:
        print(f"  → 模型名 '{app_config.llm.model_name}' 可能不存在")
        print("     DeepSeek 官方 API 的模型名通常是 deepseek-chat / deepseek-reasoner")
    elif "402" in msg or "Insufficient Balance" in msg:
        print("  → 账户余额不足，去 DeepSeek 平台充值")
    elif "Connection" in msg or "Timeout" in msg or "getaddrinfo" in msg:
        print("  → 网络不通。检查网络/代理，或确认能访问 api.deepseek.com")
    else:
        print("  → 无法归类，请把上面的原始信息发出来")


if __name__ == "__main__":
    print_config()
    try:
        test_invoke()
        test_stream()
        print("连接测试通过 [OK]")
    except Exception as e:
        diagnose(e)
