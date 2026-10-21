# -*- coding: utf-8 -*-
"""代码生成与执行工具（内置自动纠错，最多重试 3 次）。"""
import json

from langchain_core.tools import tool

from app.config import get_settings
from app.core.logger import get_logger
from tasks.analysis_tasks import execute_code_task

settings = get_settings()
logger = get_logger("agent.code_tool")

MAX_RETRY = 3  # 自动纠错最大重试次数


def build_code_tool(data_file_path: str, file_type: str, llm):
    """构建代码执行工具，绑定数据集文件与用于纠错的 LLM。"""

    @tool
    def code_tool(code: str, goal: str) -> str:
        """在沙箱中执行 pandas/numpy 分析代码并返回计算结果。

        Args:
            code: 要执行的 Python 代码。直接使用已加载的 `df`、`pd`、`np`，最终结果赋值给 `result`。
            goal: 这段代码要完成的分析目标（用于执行失败时自动纠错）。
        """
        current_code = code
        last_error = None

        for attempt in range(1, MAX_RETRY + 1):
            # 通过 Celery 队列执行（本地 eager 模式同步执行，生产 redis 异步）
            try:
                res = execute_code_task.delay(data_file_path, file_type, current_code).get(
                    timeout=settings.sandbox_timeout + 15
                )
            except Exception as e:  # 队列/超时等异常
                res = {"status": "error", "error": f"任务执行异常：{e}", "result": None,
                       "stdout": "", "stderr": "", "execution_time": 0}

            if res.get("status") == "success":
                return json.dumps({
                    "status": "success",
                    "execution_time": res.get("execution_time"),
                    "stdout": res.get("stdout", ""),
                    "result": res.get("result"),
                }, ensure_ascii=False, default=str)

            last_error = res.get("error") or "未知错误"
            logger.debug("代码执行失败（第 %d 次）：%s", attempt, last_error)
            if attempt < MAX_RETRY:
                # 自动纠错：把报错信息回传 LLM 生成修正后的代码
                current_code = _repair_code(llm, current_code, goal, last_error)

        return json.dumps({
            "status": "error",
            "error": f"代码执行失败（已自动重试 {MAX_RETRY} 次）：{last_error}",
        }, ensure_ascii=False)

    return code_tool


def _repair_code(llm, code: str, goal: str, error: str) -> str:
    """让 LLM 根据报错信息修正代码。"""
    prompt = (
        "下面这段 pandas 数据分析代码执行时报错了，请根据报错信息修正代码，"
        "只输出修正后的完整 Python 代码（不要任何解释）。\n\n"
        f"分析目标：{goal}\n\n"
        f"原代码：\n```python\n{code}\n```\n\n"
        f"报错信息：{error}\n\n"
        "注意：直接使用已加载的 df/pd/np，最终结果赋值给 result，禁止联网、读写文件与系统调用。"
    )
    try:
        resp = llm.invoke(prompt)
        text = resp.content if hasattr(resp, "content") else str(resp)
        return _extract_code(text)
    except Exception:
        return code  # LLM 不可用时返回原代码（由下一次重试兜底）


def _extract_code(text: str) -> str:
    """从 LLM 输出中提取 ```python ... ``` 代码块。"""
    if "```" in text:
        parts = text.split("```")
        for i in range(1, len(parts), 2):
            block = parts[i]
            if block.startswith("python"):
                block = block[6:]
            block = block.strip()
            if block:
                return block
    return text.strip()
