# Job Skill Initial Content Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立覆盖完整求职流程的仓库介绍，并把 `interview-deep-review` 作为首个可发现、可理解、可校验的子 Skill 纳入仓库。

**Architecture:** 根 README 负责仓库级定位和 Skill 导航；每个 `skills/<name>/README.md` 面向使用者解释能力；同目录 `SKILL.md` 面向 Agent 提供执行约束。首版不引入安装脚本、站点或 CI。

**Tech Stack:** Markdown、Git、Codex Skill YAML frontmatter、Skill Creator `quick_validate.py`

## Global Constraints

- 仓库定位覆盖职业定位、简历、投递、面试准备、面试复盘和 Offer 决策等完整求职流程。
- 必须区分仓库规划与当前已提供能力；首版只有 `interview-deep-review`。
- 逐字稿事实、分析推断和未知信息必须分开表达。
- 没有转写工具时请求用户提供逐字稿，不得假装完成转写。
- 面试评分与面试官信号只能作为辅助判断，不得表述为确定结论。
- 仓库介绍以“祝大家求职顺利，拿到心仪的 Offer”收尾。

---

### Task 1: 仓库级介绍

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: 已确认的仓库定位与目录约定。
- Produces: 仓库入口、求职流程能力地图、现有 Skill 索引、使用方式和贡献约定。

- [ ] **Step 1: 编写根 README**

写入以下信息层级：标题与一句话定位；“为什么建这个仓库”；覆盖完整求职流程的六阶段能力地图；“当前已收录”表格；通用安装和调用示例；目录结构；贡献说明；求职祝福。当前能力表只列 `interview-deep-review`，并链接到 `skills/interview-deep-review/README.md`。

- [ ] **Step 2: 校验事实边界和链接**

Run: `rg -n "interview-deep-review|职业定位|简历|投递|面试准备|面试复盘|Offer|祝大家求职顺利" README.md`

Expected: 每个定位关键词均有匹配，当前 Skill 链接指向存在的目标路径。

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: introduce the job skill collection"
```

### Task 2: 面试深度复盘 Skill

**Files:**
- Create: `skills/interview-deep-review/README.md`
- Create: `skills/interview-deep-review/SKILL.md`

**Interfaces:**
- Consumes: 压缩包中的原始 `interview-deep-review/SKILL.md`，仅作为内容素材。
- Produces: 面向使用者的功能介绍，以及面向 Agent 的规范 Skill 入口。

- [ ] **Step 1: 编写 Skill README**

README 必须包含：能力定位、适用场景、所需输入、交付内容、七步工作流、证据边界、安装方式、调用示例和适用限制。明确“有逐字稿可做深度复盘；只有回忆材料时只能做有限复盘”。

- [ ] **Step 2: 规范化 SKILL.md**

保留原素材中全场扫描、逐题拆解、专项分析、系统诊断、下一轮备战和行动清单的有效方法；压缩重复表达，并增加以下硬约束：

```markdown
- 将内容标为“逐字稿事实”“分析推断”或“信息不足”。
- 引用时间戳和原话时只使用输入中真实存在的信息。
- 不根据“好的”“明白”等单一话语确定面试结果。
- 未经用户提供或联网验证，不编造公司、岗位或行业最新动态。
- 未获得逐字稿时先说明复盘深度限制。
```

frontmatter 使用名称 `interview-deep-review`，description 同时说明能力和触发场景，不使用引号包裹整个字段。

- [ ] **Step 3: 运行 Skill 校验**

Run: `python3 /Users/chenyufan/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/interview-deep-review`

Expected: `Skill is valid!`

- [ ] **Step 4: Commit**

```bash
git add skills/interview-deep-review/README.md skills/interview-deep-review/SKILL.md
git commit -m "feat: add interview deep review skill"
```

### Task 3: 仓库级验收与发布

**Files:**
- Verify: `README.md`
- Verify: `skills/interview-deep-review/README.md`
- Verify: `skills/interview-deep-review/SKILL.md`

**Interfaces:**
- Consumes: Task 1 和 Task 2 的全部交付物。
- Produces: 可浏览、无无关产物、已推送到 GitHub `main` 的首版仓库。

- [ ] **Step 1: 检查 Markdown 和目录引用**

Run: `git diff --check HEAD~2..HEAD && test -f README.md && test -f skills/interview-deep-review/README.md && test -f skills/interview-deep-review/SKILL.md`

Expected: 退出码为 0，无空白错误，三个文件均存在。

- [ ] **Step 2: 检查敏感或无关产物**

Run: `find . -path ./.git -prune -o -type f -print | sort`

Expected: 只出现设计/计划文档、根 README 和 Skill 目录内的 README、SKILL 文件；不出现 zip、`.DS_Store`、凭据或临时文件。

- [ ] **Step 3: 检查仓库状态和提交历史**

Run: `git status --short --branch && git log --oneline --decorate -5`

Expected: 工作树干净，提交历史包含设计、计划、仓库介绍和 Skill 四类改动。

- [ ] **Step 4: 推送并核验远端**

```bash
git push -u origin main
git ls-remote --heads origin main
```

Expected: 推送成功，远端 `refs/heads/main` 指向本地 `HEAD`。
