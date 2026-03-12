# Skill Audit & Installation Plan

**System Capabilities Verified:**
- ✅ git 2.47.1
- ✅ gh 2.64.0 (GitHub CLI)
- ✅ node v24.14.0
- ✅ npm 11.9.0
- ✅ python 3.11.9
- ❌ curl (but Invoke-WebRequest available as replacement)

---

## Tier 1 (Business Critical - Install Now)

| Skill | Status | Value | Why |
|-------|--------|-------|-----|
| **gh-issues** | Ready | 🔴 HIGH | Auto-fix GitHub issues, spawn sub-agents for PRs, orchestrate dev work |
| **github** | Ready | 🔴 HIGH | PR status, CI runs, code review, issue management |
| **coding-agent** | Ready | 🔴 HIGH | Delegate coding to Claude Code/Codex - multiplies capability |
| **skill-creator** | Ready | 🟠 MED-HIGH | Build custom skills for gaps |
| **discord** | Ready | 🔴 HIGH | Already available - automated notifications/check-ins |

## Tier 2 (Expand Capabilities - Install Next 2h)

| Skill | Status | Value | Why |
|-------|--------|-------|-----|
| **notion** | Verify | 🟠 MEDIUM | Knowledge base, project tracking |
| **obsidian** | Verify | 🟠 MEDIUM | Local knowledge base alternative |
| **slack** | Verify | 🟡 LOW | Slack messaging (you prefer Discord) |
| **model-usage** | Verify | 🟡 LOW | Monitor token spend & model usage |
| **healthcheck** | Verify | 🟡 LOW | System monitoring, OpenClaw health |

## Tier 3 (Not Feasible on Windows)

| Skill | Issue |
|-------|-------|
| **summarize** | Requires `summarize` binary (brew only) |
| **sherpa-onnx-tts** | Requires ONNX runtime (complex setup) |
| **things-mac** | macOS only |
| **imsg** | macOS only |
| **apple-notes/reminders** | macOS only |

---

## Installation Timeline

- **Now (18:45):** Test gh-issues + github skills
- **19:00:** Test coding-agent
- **19:15:** Test skill-creator + notion/obsidian
- **19:30:** Complete audit, report findings to Firas

**Expected outcome:** Unlock GitHub automation, code collaboration, and knowledge management. Capability score: 45→70+
