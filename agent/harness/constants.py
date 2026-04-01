#!/usr/bin/env python3
"""
Git 规范常量
"""


class GitPrefixes:
    """Git Commit 前缀规范 - 用于SoftLimit提示和HardLimit验证"""
    RESEARCH = "[research]:"
    REPORT = "[report]:"
    DOC = "[doc]:"
    SESSION = "[session]:"
    STATE = "[state]:"
    GATE = "[gate]:"
    MAP = "[map]:"
    MECHANISM = "[mechanism]:"
    PATH = "[path]:"
    META = "[meta]:"
    SYNC = "[sync]:"
    INIT = "[init]:"
    
    ALL = [RESEARCH, REPORT, DOC, SESSION, STATE, GATE, 
           MAP, MECHANISM, PATH, META, SYNC, INIT]
