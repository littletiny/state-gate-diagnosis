---
name: summary
description: SUM - Summary Report Generator. Generate final reports by consolidating analysis documents from CR, CMR, Explore and other stages. Use when analysis is complete and a final report needs to be produced.
---

# Summary Report Generator

Consolidate multi-stage analysis outputs into a final report.

## Input Sources

Read available analysis documents:
- `knowledge/states/*.md`, `knowledge/paths/*.md`, `knowledge/gates/*.md`, `knowledge/maps/*.md` - Explore outputs
- `knowledge/research-log.md` - Research history

## Output

Single file: `knowledge/final-report.md`

## Report Content

Include these elements (organize freely based on available inputs):

**Context**
- Analysis goal and scope
- Methodology used (CR/CMR/Explore/...)

**Key Findings**
- Architecture overview (if CR available)
- Critical mechanisms (if CMR available)
- States/Gates discovered (if Explore available)
- Important discoveries and insights

**Issues & Risks**
- Identified problems with severity
- Potential risks

**Recommendations**
- Actionable items with priority
- Next steps / follow-up work

**References**
- Inline citations to source documents
- Key code locations

## Guidelines

- Executive summary last: Write it after completing the report body
- Dynamic structure: Skip sections if no relevant input exists
- No fixed template: Organize content in the most readable way
- Every conclusion must cite its source
