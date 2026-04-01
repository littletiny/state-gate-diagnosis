---
name: summary
description: SUM - Summary Report Generator. Generate structured final reports by consolidating analysis documents from CR, CMR, Explore and other stages. Use when the analysis is complete and a final summary report needs to be produced.
---

# Summary Report Generator

Generate a consolidated final report from multi-stage analysis outputs.

## Quick Start

```bash
# List all analysis documents to consolidate
ls doc/*.md knowledge/*/*.md knowledge/*.md 2>/dev/null
```

Generate report: `knowledge/final-report.md`

## Workflow

### Step 1: Collect Inputs

Read all analysis documents:
- `doc/*.md` - CR/CMR architecture and mechanism docs
- `knowledge/states/*.md` - States discovered during Explore
- `knowledge/gates/*.md` - Gates discovered during Explore
- `knowledge/maps/*.md` - Topology maps from Explore
- `knowledge/research-log.md` - Research log

### Step 2: Extract Key Information

For each document:
- Identify document type (architecture/mechanism/state/gate/map)
- Extract core conclusions
- Record key references (file paths, line numbers)

### Step 3: Generate Report

See [references/report-template.md](references/report-template.md) for the 8-section structure:

1. Executive Summary - Core findings in 3-5 sentences
2. Background & Scope - Goals, scope, methodology
3. Architecture Overview - Tech stack, layers, components
4. Key Mechanisms - Critical mechanisms from CMR
5. Deep Dive Findings - States, Gates, discoveries
6. Issues & Risks - Identified problems and risks
7. Conclusions & Recommendations - Actionable items with priorities
8. References - All source documents and code references

### Step 4: Finalize

- Write to `knowledge/final-report.md`
- Update `knowledge/research-log.md`
- Git commit: `[summary]: Generate final analysis report`

## Quality Checklist

- [ ] Executive summary conveys core info in 30 seconds
- [ ] Every conclusion has a traceable reference
- [ ] Recommendations are specific, actionable, prioritized
- [ ] No new analysis - only consolidation of existing work
