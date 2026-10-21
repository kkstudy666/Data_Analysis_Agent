# -*- coding: utf-8 -*-
"""Agent 组装：创建绑定指定数据集的 OpenAI 工具调用 Agent。"""
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agent.llm import get_llm
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools.chart_tool import chart_tool
from app.agent.tools.code_tool import build_code_tool
from app.agent.tools.metadata_tool import build_metadata_tool
from app.agent.tools.report_tool import report_tool


def build_agent(data_file_path: str, file_type: str, meta_info: dict,
                provider: str = "ollama") -> AgentExecutor:
    """构建绑定指定数据集的 Agent 执行器。

    - 流式 LLM 用于主循环（SSE 推送思考过程）；
    - 非流式 LLM 用于 code_tool 内部自动纠错；
    - 工具按数据集上下文动态构建；
    - provider 指定模型提供商：ollama（本地）/ deepseek（云端 API）。
    """
    llm = get_llm(provider=provider, streaming=True)
    repair_llm = get_llm(provider=provider, streaming=False)

    tools = [
        build_metadata_tool(meta_info),
        build_code_tool(data_file_path, file_type, repair_llm),
        chart_tool,
        report_tool,
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=15,
        verbose=False,
        handle_parsing_errors=True,
    )
