# -*- coding: utf-8 -*-
"""元数据查询工具。"""
import json

from langchain_core.tools import tool


def build_metadata_tool(meta_info: dict):
    """构建绑定具体数据集的元数据查询工具（闭包捕获 meta_info）。"""

    @tool
    def metadata_tool() -> str:
        """查询当前数据集的字段名称、数据类型、行数、列数、每列缺失值、重复行、异常值与清洗建议。"""
        return json.dumps(meta_info, ensure_ascii=False, indent=2)

    return metadata_tool
