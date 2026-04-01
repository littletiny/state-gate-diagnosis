#!/usr/bin/env python3
"""
探索工具集 - 极简版本

设计原则：
1. Agent 直接使用 shell 命令（git/ls/cat/grep）查询信息
2. 只保留必要的路径解析和 frontmatter 处理
3. 透明、简单、可预测
"""

from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import re


def get_working_dir(knowledge_dir: str = "knowledge") -> Path:
    """
    获取当前工作目录。
    优先使用新结构：knowledge/sessions/current/working/
    兼容旧结构：knowledge/
    """
    current = Path(knowledge_dir) / "sessions" / "current" / "working"
    if current.exists():
        return current
    return Path(knowledge_dir)


def doc_path(doc_type: str, name: str, knowledge_dir: str = "knowledge") -> Optional[Path]:
    """
    返回文档的完整路径，如果不存在返回 None。
    Agent 也可以直接用：cat knowledge/sessions/current/working/{type}s/{name}.md
    """
    path = get_working_dir(knowledge_dir) / f"{doc_type}s" / f"{name}.md"
    return path if path.exists() else None


def read_doc(doc_type: str, name: str, knowledge_dir: str = "knowledge") -> Optional[str]:
    """读取文档内容，如果不存在返回 None"""
    path = doc_path(doc_type, name, knowledge_dir)
    if path:
        return path.read_text(encoding='utf-8')
    return None


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    解析 frontmatter，返回 (metadata, body)
    
    示例：
        ---
        status: discovered
        tags: tcp, congestion
        ---
        # Title
        Content...
    """
    metadata = {}
    body = content
    
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            body = parts[2].strip()
            
            # 简单解析 key: value 格式
            for line in fm_text.split('\n'):
                if ':' in line and not line.strip().startswith('#'):
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
    
    return metadata, body


def write_doc(doc_type: str, name: str, content: str, 
              metadata: Optional[Dict[str, Any]] = None,
              knowledge_dir: str = "knowledge") -> Path:
    """
    写入文档，可选添加 frontmatter
    """
    dir_path = get_working_dir(knowledge_dir) / f"{doc_type}s"
    dir_path.mkdir(parents=True, exist_ok=True)
    
    path = dir_path / f"{name}.md"
    
    if metadata:
        fm_lines = ['---']
        for key, value in metadata.items():
            if isinstance(value, list):
                fm_lines.append(f"{key}: {', '.join(value)}")
            else:
                fm_lines.append(f"{key}: {value}")
        fm_lines.append('---')
        fm_lines.append('')
        content = '\n'.join(fm_lines) + content
    
    path.write_text(content, encoding='utf-8')
    return path


def get_current_session_dir(knowledge_dir: str = "knowledge") -> Optional[Path]:
    """
    获取当前会话目录（通过 current 软链接）
    """
    current_link = Path(knowledge_dir) / "sessions" / "current"
    if current_link.exists() and current_link.is_symlink():
        return current_link.resolve()
    return None


# ============ 便捷函数（可选使用） ============

def doc_exists(doc_type: str, name: str, knowledge_dir: str = "knowledge") -> bool:
    """检查文档是否存在"""
    return doc_path(doc_type, name, knowledge_dir) is not None


def get_doc_status(doc_type: str, name: str, knowledge_dir: str = "knowledge") -> Optional[str]:
    """获取文档的 status（从 frontmatter）"""
    content = read_doc(doc_type, name, knowledge_dir)
    if content:
        metadata, _ = parse_frontmatter(content)
        return metadata.get('status')
    return None


if __name__ == "__main__":
    # 简单测试
    print("Working dir:", get_working_dir())
    print("Current session:", get_current_session_dir())
