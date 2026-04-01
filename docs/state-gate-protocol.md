# State-Gate Trace Protocol

## Overview

A multi-phase pipeline methodology for exploring resource flow control systems.
Each phase runs as a separate Agent, reading documents from previous phases.

Core Model:
- **State**: Discrete state nodes in a system dimension. A State has clear semantic boundaries (distinguishable from other states), observability (logic exists to check/record it), and transition conditions (entry/exit triggers).
- **Gate**: Decision points for state transitions. Given current State + context, determines allow/reject/delay/divert and produces next State + side effects (Action).
- **Action**: Side effects produced by Gate decision. Causal chain: `State → [Gate decision] → Action → [may cause] → State'`. Action may include immediate handling of current request, state transition, propagated effects to other components, and resource operations.

State Driver Types (orthogonal, combinable; can form Hybrid drivers):
- **Condition-Driven**: Boolean condition satisfaction triggers transition (e.g., threshold crossed, predicate true, guard condition met)
- **Message-Driven**: Message/signal reception triggers transition (e.g., protocol message, control signal, interrupt, timeout notification)

## Phase 1: Discovery

Purpose: Scan code to discover State and Gate instances.

Agent 能力: 代码扫描 + 机制分析

> 使用系统级 Skills（由 Agent 平台提供）：
> - **CR (code-reader)**: 模块结构扫描，生成高层架构文档
> - **CMR (code-mechanism-reader)**: 深入特定机制分析，关注概念抽象、状态机、同步/异步设计

Input: Source code directory

Output: `doc/state-gate/states/{name}.md`, `doc/state-gate/gates/{name}.md` with `status: discovered`

Discovery Checklist:
- State: Find discrete state nodes (Condition-Driven or Message-Driven)
- Gate: Find decision points that read State and produce Action

## Phase 2: Analysis

Purpose: Deep analysis of discovered State/Gate instances.

Agent Type: Generic

Input: states/*.md, gates/*.md with status=discovered

Output: Updated documents with status=analyzed

State Analysis Checklist:
- Semantics: What does this state represent? How to distinguish from adjacent states?
- Driver: Condition-Driven / Message-Driven / Hybrid?
- Entry: What conditions trigger transition into this state?
- Exit: What conditions trigger transition out of this state?
- Gates: Which Gates check this State? What decisions depend on it?
- Abnormal: What happens when State transition fails or gets stuck?

Gate Analysis Checklist:
- Trigger: When is this gate evaluated? (state_change | condition_met | message_received | timeout)
- Condition breakdown: What criteria is checked? (state check, threshold comparison, compound condition)
- Source: Where do criteria values come from? (hardcoded | sysctl | computed | state_registry)
- Action analysis: What happens after decision? Recovery path?
- Sensitivity: Easy to trigger? Under what conditions?

## Phase 3: Connection

Purpose: Build State-Gate topology relationships.

Agent Type: Generic

Input: states/*.md, gates/*.md with status=analyzed

Output: maps/{module}.md

Connection Checklist:
- State hierarchy: high-level vs low-level states, state machine nesting
- State machine cycles: loops in state transitions
- Gate cascading: gate A triggers -> affects gate B
- Critical paths: entry to exit control chains

## Phase 4: Diagnosis

Purpose: Trace root cause along State-Gate graph.

Agent Type: Generic

Input: maps/{module}.md + symptom description

Output: paths/{symptom}_diagnosis.md

Output Specification:
- **Purpose**: Executable diagnostic procedures for specific symptoms
- **Content**: Step-by-step decision trees starting from symptom, traversing State-Gate graph to root cause
- **Evidence**: Each step must reference code locations (file:line) or data points
- **Structure**: Symptom → Starting State → Hypothesis paths → Verification steps → Root cause identification
- **Status**: `done` (diagnosis complete) or `partial` (inconclusive, needs more data)

Diagnosis Method (ECTM):

**Core Principles**:
- **Observer Check**: Question "obvious" assumptions; verify the observation framework itself is unbiased
- **Counter-Intuitive Hypothesis**: Must include at least one hypothesis that contradicts intuition, combating cognitive fixation
- **Mechanism over Symptom**: Don't stop at "what broke"; find the causal chain of "how it broke"
- **Evidence-Driven**: All conclusions must include code references (file:line)
- **Value of Outliers**: Unexplained details often reveal the true root cause

**Flow**: Observer Check → Problem Evolution → Hypothesis Expansion → Mechanism Audit → Evidence-Driven Deep Dive → Global Consistency Audit

Root Cause Levels:
- Direct: Which Gate triggered the symptom?
- Intermediate: Why did the triggering condition or message occur?
- Deep: Why did State become abnormal? (imbalance? config? bug?)

## Execution Guide

Trigger Conditions:
- No prior docs exist -> Start Phase 1
- Found status=discovered docs -> Start Phase 2
- Multiple status=analyzed docs -> Start Phase 3
- Have map + symptom -> Start Phase 4

Pipeline Rules:
- One Agent per phase
- Agent reads input docs, writes output docs, exits
- Next phase triggered by presence of appropriate status docs
- New discoveries reset to Phase 1 for that component

## ECTM Integration

| Phase | Observe | Hypothesize | Verify | Evidence |
|-------|---------|-------------|--------|----------|
| Discovery | Code patterns | This is State/Gate | code-mechanism-reader 分析 | Code locations |
| Analysis | State/Gate behavior | Abnormal patterns | Code reading | Key code + logic |
| Connection | Document relations | Impact paths | Cross-module read | Call relations |
| Diagnosis | Symptom | Multiple paths | Gate trigger check | Decision path |
