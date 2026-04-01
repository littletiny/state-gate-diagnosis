"""
探索工具集 - 知识库工具（简化版）

Agent 直接使用 shell 命令（git/ls/cat/grep）查询信息。
本模块只提供必要的路径解析和 frontmatter 处理。
"""

from .exploration_tools import (
    get_working_dir,
    get_current_session_dir,
    doc_path,
    read_doc,
    write_doc,
    doc_exists,
    get_doc_status,
    parse_frontmatter,
)

__all__ = [
    # 路径解析
    "get_working_dir",
    "get_current_session_dir",
    "doc_path",
    # 文档读写
    "read_doc",
    "write_doc",
    "doc_exists",
    "get_doc_status",
    # frontmatter 处理
    "parse_frontmatter",
]
