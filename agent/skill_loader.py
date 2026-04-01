#!/usr/bin/env python3
"""
极简 Skill 路径提供器 - 只检查目录是否存在

模型会自己读取和解析 skill 目录中的内容。
"""

from pathlib import Path


def get_skill_path(skill_name: str, skills_dir: str = "skills") -> str:
    """
    获取 skill 目录路径
    
    返回空字符串如果 skill 不存在。
    模型会自己读取目录中的内容。
    """
    skill_path = Path(skills_dir) / skill_name
    
    if skill_path.exists() and skill_path.is_dir():
        return str(skill_path)
    
    return ""


def list_skills(skills_dir: str = "skills") -> list[str]:
    """列出所有可用的 skill 名称（目录名）"""
    skills_path = Path(skills_dir)
    
    if not skills_path.exists():
        return []
    
    skills = []
    for item in skills_path.iterdir():
        if item.is_dir():
            skills.append(item.name)
    
    return sorted(skills)
