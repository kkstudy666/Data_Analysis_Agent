# -*- coding: utf-8 -*-
"""代码执行沙箱：subprocess 启动受限子进程执行用户代码。

安全策略（进程级沙箱）：
1. `python -I` 隔离模式：隔离当前目录与用户环境变量，防止恶意模块注入；
2. 子进程内 resource.setrlimit：限制 CPU / 内存 / 文件数 / 进程数；
3. sys.addaudithook：import 白名单、禁止网络、禁止危险系统调用、限制文件读写；
4. 独立临时工作目录，执行后清理；结果结构化回传。
"""
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from app.config import get_settings
from app.core.exceptions import ValidationError
from app.sandbox.allowlist import is_allowed

settings = get_settings()

RUNNER = str(Path(__file__).parent / "runner_template.py")


def _check_imports(code: str) -> None:
    """AST 静态检查（第一道防线）：仅允许导入白名单模块。"""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValidationError(f"代码存在语法错误：{e.msg}（第 {e.lineno} 行）")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if not is_allowed(top):
                    raise ValidationError(f"沙箱禁止导入模块：{top}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                if not is_allowed(top):
                    raise ValidationError(f"沙箱禁止导入模块：{top}")


def execute_code(data_file_path: str, file_type: str, code: str) -> dict:
    """在沙箱中执行用户代码，返回标准化结果结构。

    返回结构：
    {
        status: "success" | "error" | "timeout",
        stdout: str, stderr: str,
        result: dict | None,       # 子进程回传的结构化结果
        error: str | None,
        execution_time: float,
    }
    """
    _check_imports(code)
    # 数据文件转绝对路径，避免子进程 cwd=workdir 时相对路径失效
    data_file_path = os.path.abspath(data_file_path)

    workdir = tempfile.mkdtemp(prefix="sandbox_")
    code_file = os.path.join(workdir, "user_code.py")
    result_file = os.path.join(workdir, "result.json")

    env = os.environ.copy()
    env["SANDBOX_TIMEOUT"] = str(settings.sandbox_timeout)
    env["SANDBOX_MAX_MEMORY_MB"] = str(settings.sandbox_max_memory_mb)
    env["SANDBOX_WORKDIR"] = workdir  # 临时工作目录（供子进程写路径白名单判断）
    env["MPLCONFIGDIR"] = workdir  # matplotlib 缓存写入临时目录

    try:
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)

        cmd = [sys.executable, "-I", RUNNER, data_file_path, file_type, code_file, result_file]
        start = time.time()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.sandbox_timeout + 5,
                cwd=workdir,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "stdout": "",
                "stderr": "",
                "result": None,
                "error": f"代码执行超过 {settings.sandbox_timeout}s，已被强制终止",
                "execution_time": round(time.time() - start, 3),
            }

        execution_time = round(time.time() - start, 3)
        stdout = (proc.stdout or "")[:5000]
        stderr = (proc.stderr or "")[:5000]

        # 读取子进程回传的结构化结果（result.json 内容为 {status, result, error}）
        result_data = None
        result_error = None
        if os.path.exists(result_file):
            try:
                with open(result_file, "r", encoding="utf-8") as f:
                    out = json.load(f)
                result_data = out.get("result")
                result_error = out.get("error")
            except Exception:
                result_data = None

        if proc.returncode == 0 and not result_error:
            status = "success"
            error = None
        else:
            status = "error"
            error = result_error or stderr.strip() or f"进程异常退出，退出码 {proc.returncode}"

        return {
            "status": status,
            "stdout": stdout,
            "stderr": stderr,
            "result": result_data,   # 序列化后的用户结果（dataframe/scalar/list/dict 等）
            "error": error,
            "execution_time": execution_time,
        }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
