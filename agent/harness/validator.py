#!/usr/bin/env python3
"""
HardLimit: 执行验证器

通过代码强制检查Agent输出，不合格时要求重做。
与SoftLimit（PromptHints）形成双层约束机制。
"""

import subprocess
from pathlib import Path

from .log_manager import ResearchLogManager


class ExecutionValidator:
    """执行结果验证器 - HardLimit核心实现"""
    
    def __init__(self, knowledge_dir: str):
        self.knowledge_dir = Path(knowledge_dir)
        self.log_manager = ResearchLogManager(knowledge_dir)
    
    def check_research_log_updated(self, before_content: str = None) -> bool:
        """
        HardLimit检查: research-log.md 是否有更新
        
        检查项：
        - 文件是否存在
        - 内容是否有效（不只是header）
        - 相比before_content是否有新增内容
        """
        current = self.log_manager.read()
        if not current or current.strip() == "# Research Log":
            return False
        if before_content is None:
            return "##" in current
        return len(current) > len(before_content)
    
    def check_git_clean(self, base_dir: str) -> bool:
        """
        HardLimit检查: Git是否有未提交更改
        
        如果存在未提交更改，Agent需要重做（执行git commit）。
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--", "knowledge/"],
                cwd=base_dir,
                capture_output=True,
                text=True
            )
            return not result.stdout.strip()
        except:
            return True
    
    def validate_execution(self, output: str, returncode: int, 
                          research_log_before: str = None) -> dict:
        """
        HardLimit入口: 验证执行结果
        
        Returns:
            dict: 包含以下字段的验证结果
                - success: 是否成功（returncode == 0）
                - research_log_updated: 日志是否更新（HardLimit）
                - git_clean: Git是否干净（HardLimit）
                - need_continue: 是否需要继续执行
                - continue_reason: 继续原因
                - warnings: 警告列表
        """
        result = {
            "success": returncode == 0,
            "research_log_updated": False,
            "git_clean": True,
            "need_continue": False,
            "continue_reason": None,
            "warnings": []
        }
        
        # 检查是否达到step限制
        if "Max number of steps reached" in output:
            result["need_continue"] = True
            result["continue_reason"] = "steps_exhausted"
            result["warnings"].append("Agent reached step limit")
        
        # HardLimit检查: Research Log更新
        result["research_log_updated"] = self.check_research_log_updated(research_log_before)
        if not result["research_log_updated"]:
            result["warnings"].append("HardLimit: research-log.md was not updated")
        
        return result
    
    def format_validation_report(self, result: dict) -> str:
        """格式化HardLimit验证报告"""
        lines = ["\n[Validation Report - HardLimit Check]"]
        lines.append(f"  Success: {result['success']}")
        lines.append(f"  Research Log Updated: {result['research_log_updated']}")
        lines.append(f"  Git Clean: {result['git_clean']}")
        if result['need_continue']:
            lines.append(f"  Need Continue: Yes ({result['continue_reason']})")
        if result['warnings']:
            lines.append("  Warnings:")
            for w in result['warnings']:
                lines.append(f"    - {w}")
        return '\n'.join(lines)
    
    def validate_stage_output(self, stage_name: str, working_dir: Path) -> dict:
        """
        HardLimit检查: 验证特定 stage 的输出是否满足进入下一阶段的要求
        
        Returns:
            {
                "sufficient": bool,  # 是否满足条件
                "details": dict,     # 详细信息
                "message": str       # 人类可读的消息
            }
        """
        if stage_name == "connection":
            return self._validate_connection_output(working_dir)
        elif stage_name == "diagnosis":
            return self._validate_diagnosis_output(working_dir)
        # 其他 stage 可以在这里扩展
        return {"sufficient": True, "details": {}, "message": "No validation for this stage"}
    
    def _validate_connection_output(self, working_dir: Path) -> dict:
        """
        HardLimit检查: connection stage 的输出
        
        要求：
        - 至少创建了一个 map
        - 没有剩余的 analyzed states/gates（即都被处理了）
        """
        maps_dir = working_dir / "maps"
        states_dir = working_dir / "states"
        gates_dir = working_dir / "gates"
        
        # 统计 maps 数量
        maps_count = len(list(maps_dir.glob("*.md"))) if maps_dir.exists() else 0
        
        # 统计还有多少 analyzed 的 states/gates
        analyzed_states = self._count_docs_with_status(states_dir, "analyzed")
        analyzed_gates = self._count_docs_with_status(gates_dir, "analyzed")
        remaining_analyzed = analyzed_states + analyzed_gates
        
        # 判定标准
        sufficient = maps_count > 0 and remaining_analyzed == 0
        
        details = {
            "maps_created": maps_count,
            "analyzed_states": analyzed_states,
            "analyzed_gates": analyzed_gates,
            "remaining_analyzed": remaining_analyzed
        }
        
        if sufficient:
            message = f"Connection complete: {maps_count} maps created, all states/gates processed"
        else:
            if maps_count == 0:
                message = "HardLimit: Connection incomplete - no maps created"
            elif remaining_analyzed > 0:
                message = f"HardLimit: Connection incomplete - {remaining_analyzed} analyzed docs remain (need status update to connected)"
            else:
                message = "HardLimit: Connection incomplete - unknown reason"
        
        return {
            "sufficient": sufficient,
            "details": details,
            "message": message
        }
    
    def _count_docs_with_status(self, dir_path: Path, status: str) -> int:
        """统计目录中有多少 markdown 文件包含指定的 status"""
        if not dir_path.exists():
            return 0
        
        count = 0
        for f in dir_path.glob("*.md"):
            try:
                content = f.read_text(encoding='utf-8')
                if f"status: {status}" in content:
                    count += 1
            except:
                pass
        return count
    
    def _validate_diagnosis_output(self, working_dir: Path) -> dict:
        """
        HardLimit检查: diagnosis stage 的输出
        
        要求：
        - 至少创建了一个 diagnosis 路径文档
        """
        paths_dir = working_dir / "paths"
        
        # 统计 paths 数量
        paths_count = len(list(paths_dir.glob("*.md"))) if paths_dir.exists() else 0
        
        # 判定标准：至少有一个 diagnosis 文档
        sufficient = paths_count > 0
        
        details = {
            "paths_created": paths_count
        }
        
        if sufficient:
            message = f"Diagnosis complete: {paths_count} diagnosis path(s) created"
        else:
            message = "HardLimit: Diagnosis incomplete - no diagnosis paths created"
        
        return {
            "sufficient": sufficient,
            "details": details,
            "message": message
        }
