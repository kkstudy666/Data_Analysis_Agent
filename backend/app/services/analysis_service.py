# -*- coding: utf-8 -*-
"""数据分析服务：SSE 流式执行 Agent，逐事件推送分析过程。"""
import json

from langchain_core.messages import AIMessage, HumanMessage

from app.agent.agent import build_agent
from app.core.logger import get_logger
from app.models.dataset import Dataset

logger = get_logger("analysis_service")


def _to_messages(history: list) -> list:
    """把前端历史消息转成 LangChain 消息列表（仅保留文本，忽略工具调用细节）。"""
    msgs = []
    for m in history or []:
        role = m.get("role")
        content = m.get("content", "")
        if role == "user" and content:
            msgs.append(HumanMessage(content=content))
        elif role == "assistant" and content:
            msgs.append(AIMessage(content=content))
    return msgs


def _parse_output(output):
    """解析工具输出（LangChain 工具返回的常为 JSON 字符串）。"""
    if isinstance(output, str):
        try:
            return json.loads(output)
        except (json.JSONDecodeError, TypeError):
            return {"text": output}
    return output


def _sse(data: dict) -> str:
    """封装为 SSE 帧。"""
    return f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


async def stream_analysis(dataset: Dataset, question: str, history: list, provider: str = "ollama"):
    """SSE 生成器：流式推送 Agent 的思考/工具调用/结果。

    事件类型：
    - thinking:    LLM 输出文本增量（思考与结论）；
    - tool_call:   开始调用工具（含 code_tool 生成的代码）；
    - tool_result: 工具执行结果（含沙箱结果、图表 option、报告）；
    - done:        分析完成。
    """
    executor = build_agent(dataset.file_path, dataset.file_type, dataset.meta_info, provider)
    chat_history = _to_messages(history)

    try:
        async for event in executor.astream_events(
            {"input": question, "chat_history": chat_history},
            version="v2",
        ):
            kind = event.get("event")

            if kind == "on_chat_model_stream":
                content = event["data"].get("chunk", None)
                if content is None:
                    continue
                delta = content.content if hasattr(content, "content") else ""
                if delta:
                    yield _sse({"type": "thinking", "delta": delta})

            elif kind == "on_tool_start":
                name = event.get("name", "")
                tool_input = event["data"].get("input", {})
                payload = {"type": "tool_call", "tool": name, "input": tool_input}
                # code_tool 单独透出代码，便于前端代码块渲染
                if name == "code_tool" and isinstance(tool_input, dict):
                    payload["code"] = tool_input.get("code", "")
                yield _sse(payload)

            elif kind == "on_tool_end":
                name = event.get("name", "")
                output = event["data"].get("output")
                yield _sse({"type": "tool_result", "tool": name, "output": _parse_output(output)})

    except Exception as e:  # noqa: BLE001
        logger.error("Agent 执行异常: %s", e, exc_info=True)
        yield _sse({"type": "error", "message": f"分析过程出现异常：{e}"})

    yield _sse({"type": "done", "content": ""})
