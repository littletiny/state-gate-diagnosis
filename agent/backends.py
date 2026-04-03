#!/usr/bin/env python3
"""
Agent Backend 抽象层 - 支持不同的 Code Agent 实现
"""

import subprocess
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


class AgentBackend(ABC):
    """Agent 后端抽象基类"""

    @abstractmethod
    def call(
        self,
        prompt: str,
        show_realtime: bool = True,
        work_dir: Optional[Path] = None,
        max_steps: int = 100,
        timeout: int = 600,
    ) -> Tuple[str, int]:
        """
        调用 Agent，返回 (output, returncode)
        """
        pass


def _run_command(
    cmd: list[str],
    prefix: str,
    show_realtime: bool,
    work_dir: Optional[Path],
    timeout: int,
) -> Tuple[str, int]:
    """公共执行逻辑"""
    start_time = time.time()
    print(f"[Backend:{prefix}] Started at {datetime.now().strftime('%H:%M:%S')}")

    try:
        cwd = str(work_dir) if work_dir else None
        if cwd:
            print(f"[Backend:{prefix}] Working directory: {cwd}")

        if show_realtime:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=cwd,
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
                    print(f"[Backend:{prefix}] Still running... ({elapsed:.0f}s elapsed)")
                    last_status_time = now

            process.wait()
            output = "\n".join(output_lines)
            returncode = process.returncode
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
            output = result.stdout if result.stdout else result.stderr
            returncode = result.returncode

        elapsed = time.time() - start_time
        print(f"[Backend:{prefix}] Completed in {elapsed:.1f}s, returncode={returncode}")
        return output, returncode

    except subprocess.TimeoutExpired:
        print(f"[Backend:{prefix}] Timeout after {timeout}s")
        return "Error: Timeout", -1
    except Exception as e:
        print(f"[Backend:{prefix}] Error: {e}")
        return f"Error: {e}", -1


class KimiBackend(AgentBackend):
    """Kimi Code CLI 后端"""

    def call(
        self,
        prompt: str,
        show_realtime: bool = True,
        work_dir: Optional[Path] = None,
        max_steps: int = 100,
        timeout: int = 600,
    ) -> Tuple[str, int]:
        cmd = [
            "kimi",
            "--print",
            "--yolo",
            "--quiet",
            "--max-steps-per-turn", str(max_steps),
            "--output-format", "text",
            "--prompt", prompt,
        ]
        return _run_command(cmd, "kimi", show_realtime, work_dir, timeout)


class ClaudeBackend(AgentBackend):
    """Claude Code 后端"""

    def call(
        self,
        prompt: str,
        show_realtime: bool = True,
        work_dir: Optional[Path] = None,
        max_steps: int = 100,
        timeout: int = 600,
    ) -> Tuple[str, int]:
        cmd = [
            "claude",
            "--print",
            "--dangerously-skip-permissions",
            prompt,
        ]
        return _run_command(cmd, "claude", show_realtime, work_dir, timeout)


class CodexBackend(AgentBackend):
    """OpenAI Codex CLI 后端"""

    def call(
        self,
        prompt: str,
        show_realtime: bool = True,
        work_dir: Optional[Path] = None,
        max_steps: int = 100,
        timeout: int = 600,
    ) -> Tuple[str, int]:
        cmd = [
            "codex",
            "--quiet",
            "--full-auto",
            prompt,
        ]
        return _run_command(cmd, "codex", show_realtime, work_dir, timeout)


class MockBackend(AgentBackend):
    """Mock 后端 - 仅打印 prompt，不实际调用 Agent（用于调试）"""

    def call(
        self,
        prompt: str,
        show_realtime: bool = True,
        work_dir: Optional[Path] = None,
        max_steps: int = 100,
        timeout: int = 600,
    ) -> Tuple[str, int]:
        print("\n" + "="*60)
        print("[MockBackend] 接收到 prompt，长度: {} chars".format(len(prompt)))
        print("="*60)
        print("\n[MockBackend] 返回成功状态（未实际执行）")
        return "Mock execution completed", 0


BACKEND_REGISTRY = {
    "kimi": KimiBackend,
    "claude": ClaudeBackend,
    "codex": CodexBackend,
    "mock": MockBackend,
}


def create_backend(name: str) -> AgentBackend:
    """通过名称创建 Backend 实例"""
    if name not in BACKEND_REGISTRY:
        raise ValueError(f"Unknown backend: {name}. Available: {list(BACKEND_REGISTRY.keys())}")
    return BACKEND_REGISTRY[name]()
