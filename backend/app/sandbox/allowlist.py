# -*- coding: utf-8 -*-
"""沙箱模块白名单（供 executor 静态 AST 检查使用）。

策略：
- 标准库：全部放行（危险操作由 runner 的 audit hook 单独拦截，如 socket/subprocess/os.system）；
- 第三方库：仅放行数据分析核心库 pandas/numpy/matplotlib 及其传递依赖。

注意：runner_template.py 以 `python -I` 隔离模式启动、无法导入项目包，
其内部内嵌了同一份白名单逻辑，两处须保持一致。
"""
import sys

# 第三方数据分析库白名单（含 numpy/pandas/matplotlib 的传递依赖）
THIRD_PARTY_MODULES: set[str] = {
    "pandas",
    "numpy",
    "matplotlib",
    # pandas 传递依赖
    "pytz",
    "dateutil",
    "six",
    "tzdata",
    # matplotlib 传递依赖
    "PIL",
    "pyparsing",
    "cycler",
    "kiwisolver",
    "packaging",
    "fonttools",
    "contourpy",
}

# 标准库顶层名（Python 3.10+ 提供，含 encodings 等）
_STDLIB: set[str] = set(getattr(sys, "stdlib_module_names", set()))
_STDLIB.update({"encodings", "importlib", "_collections_abc"})  # 兜底补充


def is_allowed(top: str) -> bool:
    """判断顶层模块名是否允许导入。"""
    return top in _STDLIB or top in THIRD_PARTY_MODULES
