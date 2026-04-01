#!/usr/bin/env python3
"""
Pipeline Runner - 基于 YAML 配置执行 Stage

架构:
  PipelineRunner (调度器)
    └── StageRunner (基类)
          ├── pre_cycle() hook
          ├── build_prompt()
          ├── call_agent()
          └── post_cycle() hook

Skill = Stage，通过 Hooks 实现特殊逻辑:
  - ExploreRunner: pre_cycle 加载 progress, post_cycle 归档/停滞检测
  - SkillRunner: 标准执行，单轮
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
import yaml
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from base_runner import AgentRunner


class StageRunner(AgentRunner):
    """统一 Stage 执行器，通过 Hooks 实现特殊逻辑"""

    def __init__(self, config: dict, global_context: dict):
        base_dir = config.get("base_dir", ".")
        task = config.get("task", "Task")
        work_dir = config.get("work_dir")  # Kimi 工作目录（可选）
        super().__init__(base_dir, task, work_dir)
        self.config = config
        self.global_context = global_context

    def get_cycle_name(self) -> str:
        name = self.config.get("name", f"stage-{self.current_cycle}")
        return f"Stage: {name} (Cycle {self.current_cycle})"

    def run_cycle(self) -> bool:
        """执行一个 cycle，支持 hooks"""
        cycle_name = self.get_cycle_name()
        print(f"\n{'='*60}")
        print(f"{cycle_name}")
        print(f"{'='*60}")

        try:
            # Pre-hook
            self.pre_cycle()

            # 标准执行流程
            prompt = self.build_prompt()

            print(f"[Calling Agent...]")
            print(f"[Prompt length: {len(prompt)} chars, max_steps={self.max_steps}]")
            print(f"\n{'='*60}")
            print("PROMPT:")
            print(f"{'='*60}")
            print(prompt)
            print(f"{'='*60}\n")

            output, returncode = self.call_agent(prompt, show_realtime=True)

            # 输出统计
            output_lines = output.count("\n") if output else 0
            print(f"[Output] {len(output)} chars, {output_lines} lines")

            # Save log
            self.save_log(output, prompt)

            # Validate
            research_log_before = self.log_manager.read()
            validation = self.validate(output, returncode, research_log_before)
            print(self.validator.format_validation_report(validation))

            # Post-hook
            self.post_cycle(output, validation)

            self.current_cycle += 1

            # 判断是否继续
            should_stop = self.should_stop(returncode, validation)
            if should_stop:
                print(f"[Stage] Stop condition met, ending stage")

            return not should_stop

        except Exception as e:
            print(f"[Stage] Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run(self, max_cycles: int = 1) -> int:
        """运行 Stage，支持多轮迭代"""
        print(f"\n{'#'*60}")
        print(f"# Stage: {self.config.get('name', 'unnamed')}")
        print(f"# Skill: {self.config.get('skill', 'unknown')}")
        print(f"# Task: {self.task}")
        print(f"# Max Cycles: {max_cycles}")
        print(f"{'#'*60}")

        try:
            for i in range(max_cycles):
                if not self.run_cycle():
                    print(f"\n[Stage] Stopping after {i+1} cycles")
                    break
            else:
                print(f"\n[Stage] Completed {max_cycles} cycles")
        except KeyboardInterrupt:
            print(f"\n[Stage] Interrupted by user")

        return self.current_cycle

    # --- Hooks (子类可重写) ---

    def pre_cycle(self):
        """执行前准备，如加载状态、检查环境"""
        pass

    def post_cycle(self, output: str, validation: dict):
        """执行后处理，如保存状态、归档、检测停滞"""
        pass

    def should_stop(self, returncode: int, validation: dict) -> bool:
        """判断是否停止迭代，返回 True 表示停止"""
        # 默认：returncode 非 0 时停止
        return returncode != 0

    # --- 子类必须实现 ---

    @abstractmethod
    def build_prompt(self) -> str:
        """构建给 Agent 的 prompt"""
        pass


class ExploreRunner(StageRunner):
    """自由探索 Stage - 通过 Hooks 实现多轮迭代、停滞检测、自动归档"""

    # Prompt 片段配置
    PROMPT_PARTS = ["identity", "methodology", "constraints"]
    """Prompt 片段列表，按顺序组合成完整 prompt"""

    def __init__(self, config: dict, global_context: dict):
        super().__init__(config, global_context)
        self.prompts_dir = self.base_dir / "agent" / "prompts"
        self.progress_file = self.knowledge_dir / "progress.json"
        self.progress: dict = {"task": self.task, "iterations": []}
        self._stagnant = False
        self._pre_hash: Optional[str] = None

    # --- Pre-hooks ---

    def pre_cycle(self):
        """加载进度，记录 pre-hash"""
        self._pre_hash = self._get_head_hash()
        self._load_progress()

    def _load_progress(self):
        if self.progress_file.exists():
            try:
                self.progress = json.loads(self.progress_file.read_text(encoding="utf-8"))
            except Exception:
                self.progress = {"task": self.task, "iterations": []}

    def _get_session_dir(self) -> Optional[Path]:
        """获取当前 session 目录，直接使用 SessionRecorder 创建的目录"""
        if self.session_recorder:
            return self.session_recorder.actual_dir
        return None

    def _get_head_hash(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.knowledge_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""

    # --- Prompt 构建 ---

    def build_prompt(self) -> str:
        """构建自由探索 prompt"""
        parts = []
        for name in self.PROMPT_PARTS:
            content = self._load_prompt_part(name)
            if content.strip():
                parts.append(content.strip())

        prompt_body = "\n\n".join(parts)
        kb = self._get_kb_snapshot()

        warning = ""
        if self._stagnant:
            warning = (
                "\n[⚠️ 警告] 最近 3 次迭代没有更新文档或研究日志。"
                "请确保本次有实质性进展。\n"
            )

        kd = self.knowledge_dir

        return f"""{prompt_body}

目标: {self.task}

当前知识库:
{kb}
{warning}
## 执行要求

1. 阅读源码，获取新的代码洞察
2. 更新或新建 `{kd}/` 下的文档（states/, gates/, maps/, paths/）
3. 在 `{kd}/research-log.md` 最前面追加本次记录
4. 执行 git add 和 git commit（git 命令已自动指向正确目录）

## 系统改进

如果你发现当前的方法论、prompt 设计或文档格式有缺陷，可以直接修改
`{self.base_dir}/agent/prompts/` 下的对应片段文件。

源码位置: {self.base_dir / 'linux-src'}
"""

    def _load_prompt_part(self, name: str) -> str:
        """加载 prompt 片段，从 prompts/ 目录读取"""
        # 优先读取 .md 文件
        md_path = self.prompts_dir / f"explore-{name}.md"
        if md_path.exists():
            return md_path.read_text(encoding="utf-8")
        
        # 兼容性：保留 .txt 文件支持
        txt_path = self.prompts_dir / f"{name}.txt"
        if txt_path.exists():
            return txt_path.read_text(encoding="utf-8")
        
        return ""

    def _get_kb_snapshot(self) -> str:
        """生成知识库状态快照"""
        lines = []
        for subdir in ["states", "gates", "maps", "paths"]:
            d = self.knowledge_dir / subdir
            if d.exists():
                files = sorted(d.glob("*.md"))
                if files:
                    lines.append(f"- {subdir}/: {len(files)} documents")
                    for f in files[:5]:
                        lines.append(f"  - {f.name}")
                    if len(files) > 5:
                        lines.append(f"  ... and {len(files) - 5} more")
        if not lines:
            lines.append("(empty)")
        return "\n".join(lines)

    # --- Post-hooks ---

    def post_cycle(self, output: str, validation: dict):
        """自动提交、归档、检查停滞"""
        # 1. 自动提交
        self._auto_commit()

        # 2. 获取变更文件列表
        docs_changed = self._get_docs_changed()
        log_updated = validation.get("research_log_updated", False)

        # 3. 归档到 session
        self._archive_to_session()

        # 4. 记录进度
        self.progress["iterations"].append(
            {
                "cycle": self.current_cycle,
                "timestamp": datetime.now().isoformat(),
                "docs_touched": docs_changed,
                "log_updated": log_updated,
            }
        )
        self._save_progress()

        print(f"[Progress] Docs touched: {len(docs_changed)}, Log updated: {log_updated}")

        # 5. 停滞检查
        self._check_stagnant()

    def _auto_commit(self) -> bool:
        """自动执行 git add + commit"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.knowledge_dir,
                capture_output=True,
                text=True,
            )
            if not result.stdout.strip():
                return True

            subprocess.run(
                ["git", "add", "."],
                cwd=self.knowledge_dir,
                capture_output=True,
                check=True,
            )

            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=self.knowledge_dir,
                capture_output=True,
            )
            if result.returncode == 0:
                return True

            msg = self._generate_commit_message()
            subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=self.knowledge_dir,
                capture_output=True,
                check=True,
            )
            print(f"[Git] Committed: {msg.split(chr(10))[0]}")
            return True
        except Exception as e:
            print(f"[Git] Auto-commit failed: {e}")
            return False

    def _generate_commit_message(self) -> str:
        """从 research-log.md 提取 commit message"""
        log_path = self.knowledge_dir / "research-log.md"
        if not log_path.exists():
            return f"Iteration {self.current_cycle}"

        content = log_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        subject = f"Iteration {self.current_cycle}"
        for line in lines:
            if line.startswith("## "):
                subject = line[3:].strip()
                break

        body_lines = []
        for line in lines[1:]:
            if line.startswith("## "):
                break
            if line.startswith("- ") or line.startswith("### "):
                body_lines.append(line)
            if len(body_lines) > 20:
                break

        body = "\n".join(body_lines) if body_lines else ""
        if body:
            return f"{subject}\n\n{body}"
        return subject

    def _get_docs_changed(self) -> list:
        """获取最近一次 commit 中变更的文件"""
        post_hash = self._get_head_hash()
        if not post_hash or post_hash == self._pre_hash:
            return []
        try:
            result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", post_hash],
                cwd=self.knowledge_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        except Exception:
            pass
        return []

    def _archive_to_session(self):
        """将 knowledge/ 根目录的文档全量同步到 session 目录"""
        session_dir = self._get_session_dir()
        if not session_dir:
            return

        archived = 0
        for subdir in ["states", "gates", "maps", "paths"]:
            src_dir = self.knowledge_dir / subdir
            dst_dir = session_dir / subdir
            if not src_dir.exists():
                continue
            dst_dir.mkdir(parents=True, exist_ok=True)
            for src_file in src_dir.glob("*.md"):
                dst_file = dst_dir / src_file.name
                if not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
                    shutil.copy2(str(src_file), str(dst_file))
                    archived += 1
        for meta in ["research-log.md", "index.md", "progress.json"]:
            src = self.knowledge_dir / meta
            dst = session_dir / meta
            if src.exists():
                if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                    shutil.copy2(str(src), str(dst))
                    archived += 1
        if archived:
            print(f"[Archive] {archived} files synced to {session_dir}")

    def _save_progress(self):
        """保存进度文件"""
        self.progress_file.write_text(
            json.dumps(self.progress, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _check_stagnant(self):
        """检查是否停滞（最近 3 次无进展）"""
        if len(self.progress["iterations"]) >= 3:
            recent = self.progress["iterations"][-3:]
            total_docs = sum(len(it["docs_touched"]) for it in recent)
            total_logs = sum(1 for it in recent if it["log_updated"])
            if total_docs == 0 and total_logs == 0:
                self._stagnant = True
                print("[HardLimit] 警告：最近 3 次迭代没有实质性进展")
            else:
                self._stagnant = False

    def should_stop(self, returncode: int, validation: dict) -> bool:
        """Explore 特殊判断：停滞时停止"""
        if returncode != 0:
            return True
        if self._stagnant:
            print("[Explore] Stagnant detected, stopping")
            return True
        return False


class SkillRunner(StageRunner):
    """普通 Skill Stage - 单轮执行"""

    def build_prompt(self) -> str:
        """读取 SKILL.md + 任务上下文"""
        skill_name = self.config.get("skill", "unknown")

        # 1. 读取 SKILL.md
        skill_paths = [
            Path.home() / ".config/agents/skills" / skill_name / "SKILL.md",
            Path(__file__).parent.parent / "skills" / skill_name / "SKILL.md",
        ]

        skill_doc = ""
        for path in skill_paths:
            if path.exists():
                skill_doc = path.read_text(encoding="utf-8")
                break

        if not skill_doc:
            skill_doc = f"# Skill: {skill_name}\n\n(No SKILL.md found)"

        # 2. 任务上下文
        task = self.config.get("task", "")
        output = self.config.get("output", "knowledge/")

        # 3. 全局上下文信息
        context_info = ""
        if self.global_context:
            context_info = "\n## Pipeline 上下文\n"
            for key, value in self.global_context.items():
                context_info += f"- {key}: {value}\n"

        return f"""{skill_doc}

---
## 当前任务

任务描述: {task}
输出位置: {output}{context_info}

## 执行要求
- 严格按照上述方法论执行
- 完成后更新研究日志
"""

    def post_cycle(self, output: str, validation: dict):
        """Skill 执行后：可更新全局上下文供后续 Stage 使用"""
        # 可选：从输出中提取关键信息更新 global_context
        pass


class PipelineRunner:
    """Pipeline 调度器 - 顺序执行 Stage"""

    # skill 到 Runner 类的映射
    RUNNER_MAP = {
        "explore": ExploreRunner,
    }

    def __init__(self, config_path: str, base_dir: str = "."):
        self.config_path = Path(config_path)
        self.base_dir = Path(base_dir).resolve()
        self.config = self._load_config()
        self.stages = self.config.get("stages", [])
        self.global_context = {}

    def _load_config(self) -> dict:
        """加载 YAML 配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return config

    def _create_runner(self, stage_config: dict) -> StageRunner:
        """创建 Stage Runner"""
        skill = stage_config.get("skill", "unknown")

        # 设置 base_dir
        stage_config["base_dir"] = str(self.base_dir)

        # 获取 Runner 类，默认 SkillRunner
        runner_cls = self.RUNNER_MAP.get(skill, SkillRunner)

        return runner_cls(stage_config, self.global_context)

    def run(self):
        """顺序执行所有 Stage"""
        print(f"\n{'#'*60}")
        print(f"# Pipeline: {self.config.get('name', 'unnamed')}")
        print(f"# Description: {self.config.get('description', 'N/A')}")
        print(f"# Total Stages: {len(self.stages)}")
        print(f"{'#'*60}")

        for i, stage_config in enumerate(self.stages):
            print(f"\n{'#'*60}")
            print(f"# Stage {i+1}/{len(self.stages)}")
            print(f"{'#'*60}")

            runner = self._create_runner(stage_config)
            max_cycles = stage_config.get("max_cycles", 1)

            cycles_run = runner.run(max_cycles)

            # Stage 结束后更新全局上下文（可选）
            self._update_global_context(stage_config, cycles_run)

        print(f"\n{'#'*60}")
        print(f"# Pipeline Completed")
        print(f"{'#'*60}")

    def _update_global_context(self, stage_config: dict, cycles_run: int):
        """Stage 结束后更新全局上下文"""
        stage_name = stage_config.get("name", "unnamed")
        self.global_context[f"{stage_name}_completed"] = True
        self.global_context[f"{stage_name}_cycles"] = cycles_run


def main():
    parser = argparse.ArgumentParser(description="Pipeline Runner")
    parser.add_argument("-c", "--config", required=True, help="Pipeline config YAML")
    parser.add_argument("-n", "--cycles", type=int, default=None, help="Override max cycles")
    parser.add_argument("-s", "--max-steps", type=int, default=100, dest="max_steps")

    args = parser.parse_args()

    # 强制使用当前工作目录作为 base_dir
    runner = PipelineRunner(args.config, base_dir=".")

    # 可覆盖 max_steps
    if args.max_steps:
        for stage in runner.stages:
            stage["max_steps"] = args.max_steps

    runner.run()


if __name__ == "__main__":
    main()
