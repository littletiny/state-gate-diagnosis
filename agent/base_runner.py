#!/usr/bin/env python3
"""
通用 Agent Runner 基类 - Harness双层约束机制

执行流程：
  pre_execute -> build_prompt(SoftLimit) -> call_agent -> validate(HardLimit) -> post_execute

Harness双层约束：
- SoftLimit: build_prompt()通过PromptHints提供规范提示、模板引导（建议遵循）
- HardLimit: validate()通过ExecutionValidator强制检查输出（不合格时重做）

子类需要实现：
  - build_prompt(): 构建特定prompt（可使用PromptHints添加SoftLimit hints）
  - get_cycle_name(): 返回当前cycle名称（Stage/Iteration）
  - pre_execute() / post_execute(): 可选hook

Agent直接使用shell命令（git/ls/cat/grep）查询信息
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

from harness import (
    ExecutionValidator, ResearchLogManager, GitCommitHarness, PromptHints
)
from session import SessionRecorder, SimpleLockManager


class AgentRunner(ABC):
    """Agent 执行器基类 - 简化版"""
    
    def __init__(self, base_dir: str, task: Optional[str] = None, work_dir: Optional[str] = None):
        self.base_dir = Path(base_dir).resolve()
        self.knowledge_dir = self.base_dir / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.task = task or "Explore"
        
        # Kimi 工作目录（可选，默认为 None 表示使用当前目录）
        self.work_dir = Path(work_dir).resolve() if work_dir else None
        
        # 核心组件（简化）
        self.log_manager = ResearchLogManager(str(self.knowledge_dir))
        self.validator = ExecutionValidator(str(self.knowledge_dir))
        self.lock_manager = SimpleLockManager(str(self.knowledge_dir), str(self.base_dir))
        self.session_recorder = None
        
        # 执行状态
        self.current_cycle = 0
        self.max_steps = 100  # 默认单次对话步数限制，可被外部设置
        self.timeout = 600
        self._session_info = None
    
    def set_max_steps(self, max_steps: int):
        """设置单次对话最大步数"""
        self.max_steps = max_steps
    
    @abstractmethod
    def build_prompt(self) -> str:
        """构建给 Agent 的 prompt，子类必须实现"""
        pass
    
    @abstractmethod
    def get_cycle_name(self) -> str:
        """获取当前 cycle 的名称，用于日志和报告"""
        return f"Cycle-{self.current_cycle}"
    
    def pre_execute(self) -> Optional[str]:
        """执行前的 hook，返回 research_log_before"""
        return self.log_manager.read()
    
    def post_execute(self, output: str, returncode: int, validation: dict):
        """执行后的 hook"""
        pass
    
    def call_agent(self, prompt: str, show_realtime: bool = True) -> Tuple[str, int]:
        """
        调用 Kimi Agent，返回 (output, returncode)
        支持实时输出以便观察进度
        """
        import time
        from datetime import datetime
        
        cmd = [
            "kimi",
            "--print",
            "--yolo",
            "--quiet",
            "--max-steps-per-turn", str(self.max_steps),
            "--output-format", "text",
            "--prompt", prompt
        ]
        
        start_time = time.time()
        print(f"[Agent] Started at {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            # 准备 cwd 参数（如果设置了 work_dir）
            cwd = str(self.work_dir) if self.work_dir else None
            if cwd:
                print(f"[Agent] Working directory: {cwd}")
            
            if show_realtime:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=cwd
                )
                
                output_lines = []
                last_status_time = start_time
                
                for line in process.stdout:
                    line = line.rstrip()
                    output_lines.append(line)
                    print(line)
                    
                    now = time.time()
                    if now - last_status_time > 30:
                        elapsed = now - start_time
                        print(f"[Agent] Still running... ({elapsed:.0f}s elapsed)")
                        last_status_time = now
                
                process.wait()
                output = '\n'.join(output_lines)
                returncode = process.returncode
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=cwd
                )
                output = result.stdout if result.stdout else result.stderr
                returncode = result.returncode
            
            elapsed = time.time() - start_time
            print(f"[Agent] Completed in {elapsed:.1f}s, returncode={returncode}")
            return output, returncode
            
        except subprocess.TimeoutExpired:
            print(f"[Agent] Timeout after {self.timeout}s")
            return "Error: Timeout", -1
        except Exception as e:
            print(f"[Agent] Error: {e}")
            return f"Error: {e}", -1
    
    def validate(self, output: str, returncode: int, research_log_before: str) -> dict:
        """
        HardLimit验证：强制检查Agent输出是否符合要求
        
        检查项：
        - returncode是否为0
        - research-log.md是否更新
        - 是否达到step限制
        
        如果检查失败，系统会构建Retry Prompt要求Agent重做。
        详见ExecutionValidator.validate_execution()。
        """
        return self.validator.validate_execution(output, returncode, research_log_before)
    
    def save_log(self, output: str, prompt: str = None):
        """保存输出到日志文件"""
        if self.session_recorder:
            log_dir = self.session_recorder.get_working_dir("logs")
        else:
            log_dir = self.knowledge_dir / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
        
        cycle_name = self.get_cycle_name()
        if cycle_name.startswith("Stage: "):
            base_name = cycle_name[7:].strip()
        elif cycle_name.startswith("Iteration "):
            base_name = f"iter{cycle_name[10:].strip()}"
        else:
            base_name = cycle_name.replace(" ", "-").lower()
        
        base_name = base_name.replace(":", "-").replace("/", "-").replace("\\", "-")
        
        log_file = log_dir / f"{base_name}.log"
        log_file.write_text(output, encoding='utf-8')
        
        if prompt:
            prompt_file = log_dir / f"{base_name}-prompt.txt"
            prompt_file.write_text(prompt, encoding='utf-8')
    
    def run_cycle(self) -> bool:
        """执行一个完整的 cycle（迭代/Stage）"""
        cycle_name = self.get_cycle_name()
        print(f"\n{'='*60}")
        print(f"{cycle_name}")
        print(f"{'='*60}")
        
        # 1. Pre-execute hook
        research_log_before = self.pre_execute()
        
        # 2. Build prompt
        prompt = self.build_prompt()
        
        # 3. Call agent
        print(f"[Calling Agent...]")
        print(f"[Prompt length: {len(prompt)} chars, max_steps={self.max_steps}]")
        print(f"\n{'='*60}")
        print("PROMPT:")
        print(f"{'='*60}")
        print(prompt)
        print(f"{'='*60}\n")
        output, returncode = self.call_agent(prompt, show_realtime=True)
        
        # 4. 输出统计
        output_lines = output.count('\n') if output else 0
        print(f"[Output] {len(output)} chars, {output_lines} lines")
        
        # 5. Save log
        self.save_log(output, prompt)
        
        # 6. Validate
        validation = self.validate(output, returncode, research_log_before)
        print(self.validator.format_validation_report(validation))
        
        # 7. Post-execute hook
        self.post_execute(output, returncode, validation)
        
        # 8. Check for continuation needed
        if validation.get('need_continue'):
            print(f"\n[Runner] Continuation needed: {validation['continue_reason']}")
        
        self.current_cycle += 1
        return returncode == 0 and not validation.get('need_continue')
    
    def run(self, max_cycles: int = 10) -> int:
        """运行多个 cycle"""
        # 获取锁
        try:
            self._session_info = self.lock_manager.acquire(self.task)
            print(f"[Lock] 获取运行锁成功")
        except RuntimeError as e:
            print(f"[Lock] 错误: {e}")
            return 0
        
        # 初始化会话记录器
        self.session_recorder = SessionRecorder(str(self.knowledge_dir), self.task)
        print(f"[Session] 会话记录器已初始化")
        
        print(f"\n{'#'*60}")
        print(f"# Agent Runner")
        print(f"# Task: {self.task}")
        print(f"# Max Cycles: {max_cycles}")
        print(f"{'#'*60}")
        
        success = False
        cycles_run = 0
        
        try:
            for i in range(max_cycles):
                cycles_run = i + 1
                if not self.run_cycle():
                    print(f"\n[Runner] Stopping after {i+1} cycles")
                    success = True
                    break
            else:
                print(f"\n[Runner] Completed {max_cycles} cycles")
                success = True
        except KeyboardInterrupt:
            print(f"\n[Runner] Interrupted by user")
        except Exception as e:
            print(f"\n[Runner] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 最终归档（移动文件并清理）
            if hasattr(self, 'finalize_session'):
                stats = {"cycles": cycles_run, "task": self.task}
                self.finalize_session(success=success, stats=stats)
            
            # 结束会话记录
            if self.session_recorder:
                stats = {"cycles": cycles_run, "task": self.task}
                self.session_recorder.finalize(success=success, stats=stats)
            
            # 释放锁
            stats = {"cycles": cycles_run, "task": self.task}
            self.lock_manager.release(success=success, stats=stats)
            if success:
                print(f"[Lock] 任务完成，已释放锁")
            else:
                print(f"[Lock] 任务失败/中断，锁文件保留")
        
        return cycles_run
