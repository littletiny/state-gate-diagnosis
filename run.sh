#!/bin/bash
# OPS 角色启动入口
#
# 两种模式:
#   1. Explore模式 (默认): 自由探索，执行 evolve.py
#   2. Pipeline模式: 顺序执行 Stage，执行 agent/pipeline.py

show_help() {
    cat << 'EOF'
Net-Diag 统一入口 (run.sh)

用法: ./run.sh [选项] [参数...]
        ./run.sh pipeline [选项] [参数...]

模式:
    (默认)              Explore 模式 - 自由探索
    pipeline            Pipeline 模式 - 顺序执行 Stage

Explore 模式示例:
    ./run.sh -n 5                    # 最多5轮迭代
    ./run.sh -t "分析TCP拥塞控制"     # 指定任务
    ./run.sh --src-dir /path/to/src -t "分析TCP"  # 指定源码目录
    ./run.sh --backend claude -t "分析网络延迟"   # 使用 Claude 后端

Pipeline 模式示例:
    ./run.sh pipeline -c rules/pipeline.yaml      # 需在项目根目录执行
    ./run.sh pipeline -c rules/pipeline.yaml -s 50

其他:
    ./run.sh --help              # 显示此帮助
    ./run.sh pipeline --help     # 显示 Pipeline 帮助
EOF
}

# 检测 Pipeline 模式
RUN_MODE="explore"
if [ "$1" = "pipeline" ]; then
    RUN_MODE="pipeline"
    shift  # 移除 'pipeline' 参数
fi

# 解析 run.sh 自己的 help (Pipeline 模式的 --help 传递给 pipeline.py)
if [ "$RUN_MODE" != "pipeline" ]; then
    for arg in "$@"; do
        case "$arg" in
            --help|-h)
                show_help
                exit 0
                ;;
        esac
    done
fi

# 让 bin/ 目录优先于系统 PATH，使 git wrap 生效
PROJECT_ROOT="$(dirname "$0")"
PATH="$PROJECT_ROOT/bin:$PATH"

if [ "$RUN_MODE" = "pipeline" ]; then
    # Pipeline 模式 - 强制使用用户当前目录作为 base_dir
    python "$PROJECT_ROOT/agent/pipeline.py" "$@"
else
    # Explore 模式
    python "$PROJECT_ROOT/bin/evolve.py" --base-dir . "$@"
fi
