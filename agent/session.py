#!/usr/bin/env python3
"""
会话管理 - SessionRecorder + SimpleLockManager
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


class SessionRecorder:
    """
    会话记录器 - 创建短 ID 命名的 session 目录
    
    Session 目录名: YYYYMMDD-HHMMSS (时间戳 ID)
    Task 信息记录在 manifest.json 和 index.json 中
    """
    
    def __init__(self, knowledge_dir: str, task: str):
        self.kb = Path(knowledge_dir).resolve()
        self.sessions_dir = self.kb / "sessions"
        self.task = task
        self.start_time = datetime.now()
        # 短 ID: 时间戳 (如 20260401-120000)
        self.session_id = self.start_time.strftime("%Y%m%d-%H%M%S")
        # 添加微秒避免同一秒内重复
        if (self.sessions_dir / self.session_id).exists():
            self.session_id = self.start_time.strftime("%Y%m%d-%H%M%S-%f")[:-3]
        
        # 创建目录结构
        self.actual_dir = self.sessions_dir / self.session_id
        self.actual_dir.mkdir(parents=True, exist_ok=True)
        
        for subdir in ["states", "gates", "maps", "mechanisms", "paths", "logs"]:
            (self.actual_dir / subdir).mkdir(exist_ok=True)
        
        # 初始化会话文件
        self._init_session_file()
        
        # 更新索引
        self._update_index()
        
        # 创建 current 软链接指向当前 session
        self._update_current_link()
    
    def _update_current_link(self):
        """创建/更新 current 软链接指向当前 session 目录"""
        link_path = self.kb / "current"
        
        # 如果已存在，先删除（可能是旧 session 的链接或文件）
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        
        # 创建新的软链接
        link_path.symlink_to(self.actual_dir, target_is_directory=True)
    
    def _init_session_file(self):
        """初始化 session.md 和 manifest.json"""
        session_file = self.actual_dir / "session.md"
        session_file.write_text(f"""# Session: {self.session_id}

**任务**: {self.task}
**开始时间**: {self.start_time.isoformat()}
**状态**: running

## 会话记录

""", encoding='utf-8')
        
        manifest = {
            "id": self.session_id,
            "task": self.task,
            "start_time": self.start_time.isoformat(),
            "status": "running",
            "stages": [],
            "documents": {"created": [], "modified": []},
            "key_findings": [],
            "references": {}
        }
        manifest_file = self.actual_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    
    def _update_index(self):
        """更新 sessions/index.json"""
        index_file = self.sessions_dir / "index.json"
        index = {}
        if index_file.exists():
            try:
                index = json.loads(index_file.read_text(encoding='utf-8'))
            except:
                pass
        
        index[self.session_id] = {
            "task": self.task,
            "start_time": self.start_time.isoformat(),
            "status": "running"
        }
        
        index_file.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding='utf-8')
    
    def _update_index_status(self, status: str, end_time, stats: dict = None):
        """更新 index.json 中的会话状态"""
        index_file = self.sessions_dir / "index.json"
        if index_file.exists():
            try:
                index = json.loads(index_file.read_text(encoding='utf-8'))
                if self.session_id in index:
                    index[self.session_id]["status"] = status
                    index[self.session_id]["end_time"] = end_time.isoformat()
                    if stats:
                        index[self.session_id]["stats"] = stats
                    index_file.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding='utf-8')
            except:
                pass
    
    def get_working_dir(self, subdir: str = None) -> Path:
        """获取工作目录路径"""
        if subdir:
            return self.actual_dir / subdir
        return self.actual_dir
    
    def record_stage(self, stage_name: str, summary: str, findings: list = None, 
                     documents: list = None, questions: list = None):
        """记录一个阶段的执行结果"""
        session_file = self.actual_dir / "session.md"
        timestamp = datetime.now().isoformat()
        
        entry = f"""### {stage_name} - {timestamp}

**摘要**: {summary}

"""
        if findings:
            entry += "**关键发现**:\n"
            for f in findings[:5]:
                entry += f"- {f}\n"
            entry += "\n"
        
        if documents:
            entry += "**相关文档**:\n"
            for doc in documents:
                entry += f"- `{doc}`\n"
            entry += "\n"
        
        if questions:
            entry += "**待解决问题**:\n"
            for q in questions[:3]:
                entry += f"- {q}\n"
            entry += "\n"
        
        entry += "---\n\n"
        
        with open(session_file, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        self._update_manifest(stage_name, findings, documents)
    
    def _update_manifest(self, stage_name: str, findings: list, documents: list):
        """更新 manifest.json"""
        manifest_file = self.actual_dir / "manifest.json"
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
            manifest["stages"].append(stage_name)
            if findings:
                manifest["key_findings"].extend(findings[:3])
            if documents:
                manifest["documents"]["created"].extend(documents)
            manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    
    def finalize(self, success: bool = True, stats: dict = None):
        """结束会话"""
        session_file = self.actual_dir / "session.md"
        manifest_file = self.actual_dir / "manifest.json"
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        status = "completed" if success else "failed"
        
        if session_file.exists():
            footer = f"""
## 会话结束

**结束时间**: {end_time.isoformat()}
**持续时间**: {duration:.0f}秒
**状态**: {status}

"""
            if stats:
                footer += "**统计**:\n"
                for k, v in stats.items():
                    footer += f"- {k}: {v}\n"
            
            with open(session_file, 'a', encoding='utf-8') as f:
                f.write(footer)
        
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
            manifest["status"] = status
            manifest["end_time"] = end_time.isoformat()
            manifest["duration_seconds"] = duration
            if stats:
                manifest["stats"] = stats
            manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # 更新 index.json 状态
        self._update_index_status(status, end_time, stats)


class SimpleLockManager:
    """
    极简文件锁管理 - 单实例运行
    
    HardLimit: 确保同时只有一个Agent实例运行
    """
    
    LOCK_FILE = "lock.file"
    STATE_FILE = "state.json"
    
    def __init__(self, knowledge_dir: str, base_dir: str = None):
        self.kb = Path(knowledge_dir).resolve()
        self.base_dir = Path(base_dir).resolve() if base_dir else self.kb.parent
        self.lock_path = self.kb / self.LOCK_FILE
        self.state_path = self.kb / self.STATE_FILE
        self.sessions_dir = self.kb / "sessions"
    
    def acquire(self, task: str) -> dict:
        """获取运行锁 - HardLimit"""
        if self.lock_path.exists():
            lock_content = self.lock_path.read_text(encoding='utf-8')
            raise RuntimeError(
                f"Agent 正在运行中 (lock.file 存在)\n"
                f"内容: {lock_content}\n"
                f"请等待完成或手动删除: {self.lock_path}"
            )
        
        # 检查上次是否失败
        if not self.state_path.exists():
            self._handle_previous_failure()
        
        # 创建锁文件
        start_time = datetime.now()
        lock_content = f"pid={os.getpid()}\ntask={task}\nstart={start_time.isoformat()}"
        self.lock_path.write_text(lock_content, encoding='utf-8')
        
        return {"task": task, "start_time": start_time, "pid": os.getpid()}
    
    def release(self, success: bool = True, stats: dict = None):
        """释放锁"""
        if success:
            # 任务成功，清理状态文件（归档已完成，无需保留状态）
            self.state_path.unlink(missing_ok=True)
            self._finalize_session(stats)
        else:
            # 任务失败/中断，保留锁文件用于恢复
            pass
    
    def _handle_previous_failure(self):
        """处理上次失败的会话"""
        # 找到最新的 session 目录（按修改时间排序）
        actual_dir = self._get_latest_session_dir()
        
        if not actual_dir or not actual_dir.exists():
            return
        
        # 更新 manifest
        manifest_file = actual_dir / "manifest.json"
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
            manifest["status"] = "failed"
            manifest["failed_at"] = datetime.now().isoformat()
            manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # 归档锁文件
        if self.lock_path.exists():
            shutil.move(str(self.lock_path), str(actual_dir / "lock.file"))
        
        self._update_sessions_index()
        print(f"[LockManager] 已标记失败会话: {actual_dir.name}")
    
    def _get_latest_session_dir(self) -> Optional[Path]:
        """获取最新的 session 目录（按修改时间排序）"""
        if not self.sessions_dir.exists():
            return None
        dirs = [d for d in self.sessions_dir.iterdir() if d.is_dir() and not d.is_symlink()]
        if not dirs:
            return None
        return sorted(dirs, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    
    def _finalize_session(self, stats: dict = None):
        """完成会话 - 仅更新锁状态，归档操作由 AgentRunner 处理"""
        actual_dir = self._get_latest_session_dir()
        
        if actual_dir and actual_dir.exists():
            print(f"[LockManager] 会话完成: {actual_dir.name}")
        
        self.lock_path.unlink(missing_ok=True)
        self._update_sessions_index()
    
    def _update_sessions_index(self):
        """更新 sessions/README.md 索引"""
        readme_path = self.sessions_dir / "README.md"
        
        sessions = []
        if self.sessions_dir.exists():
            for item in sorted(self.sessions_dir.iterdir(), reverse=True):
                if item.is_symlink():
                    continue
                if item.is_dir():
                    manifest_file = item / "manifest.json"
                    if manifest_file.exists():
                        try:
                            manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
                            sessions.append({
                                "name": item.name,
                                "task": manifest.get("task", "Unknown")[:40],
                                "status": manifest.get("status", "unknown"),
                                "stages": ", ".join(manifest.get("stages", [])[:2])
                            })
                        except:
                            pass
        
        lines = ["# Sessions Index", "", "会话历史（按时间倒序）", ""]
        lines.extend(["| 会话 | 任务 | 状态 | 阶段 |", "|------|------|------|------|"])
        
        for s in sessions[:20]:
            lines.append(f"| `{s['name']}` | {s['task']} | {s['status']} | {s['stages']} |")
        
        lines.append('')
        readme_path.write_text('\n'.join(lines), encoding='utf-8')
