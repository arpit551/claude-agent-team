# Visual Guide - Claude Agent Teams CLI

This guide shows exactly what you'll see when using the CATT CLI.

---

## 🎯 Quick Visual Tour

### 1️⃣ Initialize a Project

```bash
$ catt init
```

<details>
<summary>Click to see output</summary>

```
✓ Default config saved to /path/to/project/.catt/project.yaml
```

**What it creates:**
- `.catt/` directory
- `.catt/project.yaml` - Your team configuration
- `.catt/output/` - Agent output directory

</details>

---

### 2️⃣ View Available Teams

```bash
$ catt team list
```

<details>
<summary>Click to see output</summary>

```
                            Available Team Templates
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Team       ┃ Description                                        ┃ Roles      ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ code-rev…  │ Parallel code review                               │ Security,  │
│            │                                                    │ Perform…,  │
│            │                                                    │ Test       │
│ developm…  │ Feature development pipeline                       │ Architect, │
│            │                                                    │ Impl…,     │
│            │                                                    │ Tester     │
│ research   │ Adversarial research                               │ Investig…, │
│            │                                                    │ Devil's    │
│            │                                                    │ Advocate   │
└────────────┴────────────────────────────────────────────────────┴────────────┘
```

</details>

---

### 3️⃣ Check Your Agent Configuration

```bash
$ catt agent list
```

<details>
<summary>Click to see output</summary>

```
                            Agents
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Role            ┃ Model  ┃ Status ┃ Enabled ┃ Dependencies ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ Researcher      │ opus   │ idle   │ ✓       │ -            │
│ Manager         │ opus   │ idle   │ ✓       │ researcher   │
│ Architect       │ opus   │ idle   │ ✓       │ manager      │
│ Developer       │ sonnet │ idle   │ ✓       │ architect    │
│ Tester          │ sonnet │ idle   │ ✓       │ developer    │
│ Reviewer        │ sonnet │ idle   │ ✓       │ tester       │
└─────────────────┴────────┴────────┴─────────┴──────────────┘
```

**Color Legend:**
- 🟢 Green checkmark = Enabled
- 🔴 Status colors (idle/running/complete)
- 🔵 Model types (opus for thinking, sonnet for doing)

</details>

---

### 4️⃣ The Beautiful Kanban Board

```bash
$ catt tasks --kanban
```

<details>
<summary>Click to see output</summary>

```
╭───────────────────────── Claude Agent Teams - Tasks ─────────────────────────╮
│   📋 TODO (12)             🔄 IN PROGRESS (3)        ✅ DONE (5)             │
│                                                                              │
│   Design API endpoints     Implement auth            Setup database          │
│   Write unit tests         Write integration         Create models           │
│   Code review             Fix security bug          Add middleware          │
│   Update docs                                       Setup routes            │
│   Add logging                                       Write tests             │
│   Deploy to staging                                                         │
│   Setup monitoring                                                          │
│   Add error handling                                                        │
│   Optimize queries                                                          │
│   Add caching                                                               │
│   Security audit                                                            │
│   Performance test                                                          │
│                                                                              │
╰──────────────────────────── Progress: 25% (5/20) ────────────────────────────╯
```

**Features:**
- 📋 TODO - Not started yet
- 🔄 IN PROGRESS - Currently working
- ✅ DONE - Completed
- Progress bar at bottom
- Auto-updates from `~/.claude/todos/`

</details>

---

### 5️⃣ Preview Before Running

```bash
$ catt run --dry-run
```

<details>
<summary>Click to see output</summary>

```
╭────────────────────────────────── Project ───────────────────────────────────╮
│ my-auth-feature                                                              │
│ OAuth2 login with Google                                                     │
╰──────────────────────────────────────────────────────────────────────────────╯

Execution Plan:
  1. Researcher (opus)
  2. Manager (opus) (after: researcher)
  3. Architect (opus) (after: manager)
  4. Developer (sonnet) (after: architect)
  5. Tester (sonnet) (after: developer)
  6. Reviewer (sonnet) (after: tester)

Dry run - showing team prompt

╭──────────────────────────── Team Creation Prompt ────────────────────────────╮
│ Create an agent team to build user authentication with OAuth2.               │
│                                                                              │
│ **Team Structure:**                                                          │
│                                                                              │
│ 1. **Researcher** (opus): Research OAuth2 best practices and security.       │
│                                                                              │
│ 2. **Manager** (opus): Create task breakdown and coordinate team.            │
│                                                                              │
│ 3. **Architect** (opus): Design auth flow and system architecture.           │
│                                                                              │
│ 4. **Developer** (sonnet): Implement OAuth2 integration.                     │
│                                                                              │
│ 5. **Tester** (sonnet): Write comprehensive test suite.                      │
│                                                                              │
│ 6. **Reviewer** (sonnet): Final code review and security check.              │
│                                                                              │
│ Begin by spawning the team and coordinating their work.                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**What this shows:**
- Project name and description
- Execution order with dependencies
- Complete prompt that will be sent to Claude Code
- Model assignments per agent

</details>

---

### 6️⃣ Interactive Dashboard (Full Screen)

```bash
$ catt dashboard
```

**What you see:**

```
┌─────────────────────── Claude Agent Teams — Dashboard ───────────────────────┐
│ ⭘      Claude Agent Teams — Dashboard                            03:16:15   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 📋 TODO (12)      │ 🔄 IN PROGRESS (3)  │ ✅ DONE (5)                  │ │
│  ├──────────────────┼─────────────────────┼─────────────────────────────┤ │
│  │                  │                     │                              │ │
│  │ #task-1          │ #task-4             │ #task-7                      │ │
│  │ Design API       │ Implement auth      │ Setup database               │ │
│  │                  │ ████████░░ 80%      │                              │ │
│  │ #task-2          │                     │ #task-8                      │ │
│  │ Write tests      │ #task-5             │ Create models                │ │
│  │                  │ Write integration   │                              │ │
│  │ #task-3          │ █████░░░░░ 50%      │ #task-9                      │ │
│  │ Code review      │                     │ Add middleware               │ │
│  │                  │ #task-6             │                              │ │
│  │                  │ Fix security bug    │                              │ │
│  │                  │ ██░░░░░░░░ 20%      │                              │ │
│  └──────────────────┴─────────────────────┴─────────────────────────────┘ │
│                                                                              │
│  📊 TODO: 12  🔄 IN PROGRESS: 3  ✅ DONE: 5  📈 TOTAL: 20                   │
│  Progress: ████████████░░░░░░░░ 25%         Updated: 03:16:15              │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ q Quit  r Refresh  d Toggle Dark  t Toggle Stats                 ^p palette│
└─────────────────────────────────────────────────────────────────────────────┘
```

**Interactive Features:**
- Real-time updates
- Keyboard shortcuts (q, r, d, t)
- Progress bars for active tasks
- Color coding by status
- Auto-refresh with `--watch`

---

### 7️⃣ Tmux Agent Spawning (The Magic!)

```bash
$ catt run
```

**Creates multiple tmux windows, one per agent:**

```
┌─ Tmux: catt-agents ──────────────────────────────────────────────────────────┐
│                                                                              │
│  Windows: 0:main  1:researcher*  2:architect  3:developer  4:tester         │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  RESEARCHER AGENT (Opus)                                                    │
│                                                                              │
│  claude --model opus "You are a researcher agent..."                        │
│                                                                              │
│  🔍 Researching OAuth2 authentication patterns...                           │
│                                                                              │
│  Findings:                                                                  │
│  - OAuth2 with PKCE is recommended                                          │
│  - Use state parameter for CSRF protection                                  │
│  - Store tokens in httpOnly cookies                                         │
│  - Implement token refresh flow                                             │
│                                                                              │
│  <promise>RESEARCH_COMPLETE</promise>                                       │
│                                                                              │
│  Notifying manager...                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Switch between agents:**
- `Ctrl+B`, then `1` - Researcher
- `Ctrl+B`, then `2` - Architect
- `Ctrl+B`, then `3` - Developer
- `Ctrl+B`, then `4` - Tester
- `Ctrl+B`, then `w` - Window list

**Detach:** `Ctrl+B`, then `d`
**Reattach:** `tmux attach -t catt-agents`

---

## 🎨 Color Themes

### Light Mode
- Bright, high-contrast
- Blue headers
- Green success indicators
- Yellow warnings

### Dark Mode (Toggle with 'd')
- Easy on the eyes
- Soft colors
- Better for long sessions
- Energy efficient

---

## 📐 Layout Examples

### Compact Terminal (80x24)
```
┌─ Teams (5) ───────────────────────────────────────────────────────────┐
│ code-review │ Parallel review   │ Security, Perf, Test              │
│ development │ Feature pipeline  │ Arch, Dev, Test, Review           │
│ research    │ Adversarial       │ Investigator, Devil, Synth        │
└───────────────────────────────────────────────────────────────────────┘
```

### Wide Terminal (150x40)
```
┌──────────── Available Team Templates ────────────────────────────────────────┐
│ Team          │ Description                    │ Roles                       │
├───────────────┼────────────────────────────────┼─────────────────────────────┤
│ code-review   │ Parallel code review           │ Security Reviewer,          │
│               │                                │ Performance Analyst,        │
│               │                                │ Test Coverage Checker       │
│               │                                │                             │
│ development   │ Feature development pipeline   │ Architect, Implementer,     │
│               │                                │ Tester, Reviewer            │
│               │                                │                             │
│ research      │ Adversarial research           │ Investigator,               │
│               │                                │ Devil's Advocate,           │
│               │                                │ Synthesizer                 │
└───────────────┴────────────────────────────────┴─────────────────────────────┘
```

---

## 🎬 Video Walkthrough

*Coming soon - screencasts of each feature*

---

## 💡 Pro Tips

### 1. Split-Screen Workflow
```bash
# Terminal 1: Run agents
catt run

# Terminal 2: Monitor dashboard
catt dashboard --watch

# Terminal 3: View tmux sessions
tmux attach -t catt-agents
```

### 2. Quick Status Check
```bash
# One-liner to see everything
catt agent list && catt tasks --kanban
```

### 3. Customize Terminal
```bash
# Set colors in your shell
export CATT_THEME="dark"

# Increase terminal size
# For best experience: 150x40 or larger
```

---

## 🐛 Visual Troubleshooting

### Issue: "Garbled output"
**Solution:** Ensure terminal supports Unicode and colors
```bash
echo $TERM  # Should be xterm-256color or similar
```

### Issue: "Dashboard looks wrong"
**Solution:** Increase terminal size (minimum 80x24)

### Issue: "No colors"
**Solution:** Check terminal color support
```bash
tput colors  # Should be 256
```

---

## 📸 More Screenshots

See `SCREENSHOTS.md` for detailed CLI output examples.

---

**The visual design makes complex agent coordination feel simple!** ✨
