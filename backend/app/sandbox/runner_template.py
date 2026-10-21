# -*- coding: utf-8 -*-
"""沙箱子进程脚本（由 executor.py 以 `python -I` 隔离模式启动）。

命令行参数：<数据文件路径> <文件类型> <用户代码文件> <结果文件>
职责流程：资源限制 → 预加载数据分析库 → 安全审计钩子 → 读取数据 → 执行代码 → 回写结果。
"""
import json
import os
import sys

# ---------------------------------------------------------------------------
# 1. 资源限制（在 import 重型库之前设置，避免资源被提前占用）
# ---------------------------------------------------------------------------
try:
    import resource

    _MB = 1024 * 1024
    _timeout = int(os.environ.get("SANDBOX_TIMEOUT", "30"))
    _max_mem = int(os.environ.get("SANDBOX_MAX_MEMORY_MB", "512"))
    resource.setrlimit(resource.RLIMIT_CPU, (_timeout, _timeout + 2))           # CPU 30s
    resource.setrlimit(resource.RLIMIT_AS, (_max_mem * _MB, _max_mem * _MB))    # 内存 512MB
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))                        # 文件描述符 64
    resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))                           # 子进程数 1
    resource.setrlimit(resource.RLIMIT_FSIZE, (200 * _MB, 200 * _MB))           # 单文件 200MB
except ImportError:
    pass  # Windows 无 resource 模块，仅靠外层 timeout 兜底

# ---------------------------------------------------------------------------
# 2. 预加载数据分析库（在设置安全钩子之前，避免其复杂导入链被误伤）
# ---------------------------------------------------------------------------
import pandas as pd  # noqa: E402
import numpy as np   # noqa: E402

try:
    import matplotlib  # noqa: E402
    matplotlib.use("Agg")  # 无界面后端，不弹窗
    import matplotlib.pyplot as plt  # noqa: E402
except Exception:
    plt = None

# ---------------------------------------------------------------------------
# 3. 模块白名单与安全审计钩子（与 app/sandbox/allowlist.py 保持一致）
# ---------------------------------------------------------------------------
# 第三方数据分析库白名单（含传递依赖）
_THIRD_PARTY = {
    "pandas", "numpy", "matplotlib",
    "pytz", "dateutil", "six", "tzdata",
    "PIL", "pyparsing", "cycler", "kiwisolver", "packaging", "fonttools", "contourpy",
}
# 标准库全部放行（危险操作由 audit hook 单独拦截）
_STDLIB = set(getattr(sys, "stdlib_module_names", set()))
_STDLIB.update({"encodings", "importlib", "_collections_abc"})

# 临时工作目录（executor 通过环境变量注入，并以 cwd=workdir 启动本子进程）
WORKDIR = os.environ.get("SANDBOX_WORKDIR") or os.getcwd()


def _audit(event: str, args: tuple) -> None:
    """sys.audit 钩子：拦截危险操作。"""
    if event == "import":
        # 白名单：标准库放行 + 第三方仅限数据分析库
        name = args[0] if args else ""
        top = name.split(".")[0]
        if top and top not in _STDLIB and top not in _THIRD_PARTY:
            raise ImportError(f"沙箱禁止导入模块：{top}")
    elif event in ("socket.__new__", "socket.socket", "socket.connect",
                   "socket.getaddrinfo", "socket.bind", "socket.listen"):
        raise RuntimeError("沙箱禁止网络访问")
    elif event in ("subprocess.Popen", "os.system", "os.popen", "os.spawnl",
                   "os.spawnv", "os.execl", "os.execv", "os.posix_spawn"):
        raise RuntimeError("沙箱禁止启动子进程或系统调用")
    elif event == "open":
        path = str(args[0]) if args else ""
        mode = args[1] if len(args) > 1 else "r"
        if any(c in mode for c in "wax+"):
            # 写操作仅限临时目录（normcase 归一化 Windows 大小写/分隔符）
            abs_path = os.path.abspath(path)
            if not (os.path.normcase(abs_path).startswith(os.path.normcase(WORKDIR))
                    or abs_path.startswith("/tmp")):
                raise PermissionError("沙箱禁止写入非临时目录")
        elif any(s in path for s in ("/etc/passwd", "/etc/shadow", "id_rsa", ".ssh", ".aws", ".env")):
            raise PermissionError("沙箱禁止读取敏感文件")


sys.addaudithook(_audit)

# ---------------------------------------------------------------------------
# 4. 读取数据文件 → df
# ---------------------------------------------------------------------------
data_path, file_type, code_path, result_path = sys.argv[1:5]


def _load_df(path: str, ftype: str) -> pd.DataFrame:
    if ftype in ("xlsx", "xls"):
        return pd.read_excel(path)
    if ftype == "json":
        return pd.read_json(path)
    # CSV 使用 utf-8-sig 兼容带 BOM 与中文
    return pd.read_csv(path, encoding="utf-8-sig")


# ---------------------------------------------------------------------------
# 5. 执行用户代码并序列化结果
# ---------------------------------------------------------------------------
def _serialize(obj):
    """把结果对象转换为可 JSON 化的结构（限制返回体量）。"""
    if obj is None:
        return {"type": "none", "value": None}
    if isinstance(obj, pd.DataFrame):
        return {
            "type": "dataframe",
            "columns": [str(c) for c in obj.columns],
            "data": obj.head(100).to_dict(orient="records"),
            "shape": list(obj.shape),
        }
    if isinstance(obj, pd.Series):
        return {"type": "series", "name": str(obj.name), "data": obj.head(100).to_dict()}
    if isinstance(obj, np.integer):
        return {"type": "scalar", "value": int(obj)}
    if isinstance(obj, np.floating):
        return {"type": "scalar", "value": float(obj)}
    if isinstance(obj, (int, float, str, bool)):
        return {"type": "scalar", "value": obj}
    if isinstance(obj, dict):
        return {"type": "dict", "data": json.loads(json.dumps(obj, default=str))}
    if isinstance(obj, (list, tuple)):
        return {"type": "list", "data": json.loads(json.dumps(list(obj)[:100], default=str))}
    return {"type": "text", "value": str(obj)}


def main() -> None:
    out = {"status": "success", "result": None, "error": None}
    try:
        df = _load_df(data_path, file_type)
        # 预置命名空间：df/pd/np 可直接使用，最终结果赋值给 result
        ns = {"df": df, "pd": pd, "np": np, "plt": plt}
        with open(code_path, "r", encoding="utf-8") as f:
            code = f.read()
        exec(compile(code, code_path, "exec"), ns)
        result = ns.get("result", df)  # 未显式赋值则回传 df 预览
        out["result"] = _serialize(result)
    except Exception as e:  # noqa: BLE001 —— 捕获一切异常结构化回传
        out["status"] = "error"
        out["error"] = f"{type(e).__name__}: {e}"
    finally:
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
