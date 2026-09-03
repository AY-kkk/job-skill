# Interview Deep Review Knowledge Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `interview-deep-review` 升级为默认扫描知识缺口、满足证据条件后开展核心知识与技术深研的八步面试复盘 Skill。

**Architecture:** 保留现有证据规则和七步流程主体，在专项分析与系统性诊断之间插入证据闸门控制的知识深研阶段。`SKILL.md` 定义 Agent 行为，子集 `README.md` 面向使用者解释新增能力，根 `README.md` 只更新能力摘要；不新增脚本、依赖或测试文件。

**Tech Stack:** Markdown、YAML frontmatter、Git、Skill 规范校验器

## Global Constraints

- 每次复盘默认扫描知识缺口；只有存在逐字稿、JD 或用户指定的可定位依据时才开展深研。
- 深研主题最多五个、允许为零；同一知识块下的问题合并，不为凑数量生成内容。
- 适用范围包括产品、AI、商业化、运营等业务岗位中的技术、产品、指标、商业和行业知识。
- 保留“逐字稿事实、分析推断、信息不足”三类证据边界。
- 打断、沉默、推进语、时长、追问次数和说话比例不能单独证明回答错误或触发深研。
- 不使用固定评分阈值、固定时长比例、“二面必考”或确定性录用判断。
- 联网研究使用当前环境可用能力，不绑定特定工具或子代理；可变事实保留 URL 和查询日期。
- 外部研究不能替代对候选人经历、数字、客户和个人贡献的确认。
- 不新增脚本、测试文件、依赖、版本号文件或压缩包中虚构的关联 Skill。
- 直接更新该仓库 `main`，推送前完成规范、质量、安全和远端回读验证。

---

### Task 1: 将 Agent 工作流升级为八步法

**Files:**
- Modify: `skills/interview-deep-review/SKILL.md:1-207`

**Interfaces:**
- Consumes: 面试逐字稿或回忆笔记、JD、简历、用户目标，以及需要时检索到的公开来源。
- Produces: 含核心知识深研章节的复盘报告；材料较长或用户要求时可额外产出独立知识深研报告。

- [x] **Step 1: 保留入口与证据规则，扩充触发描述**

保持 `name: interview-deep-review`。将 frontmatter 描述改为以 `Use when` 开头的触发型描述，覆盖“复盘面试表现、分析追问和面试官信号、补齐知识缺口、准备下一轮”，不在 description 中复述八步流程。

保留“完整逐字稿、节选逐字稿、回忆笔记”的材料充分度分级，以及逐字稿事实、分析推断、信息不足三类证据规则。

- [x] **Step 2: 将流程标题与编号升级为八步**

把 `## 七步复盘流程` 改为 `## 八步复盘流程`，保留原 1—4 步，在其后新增第 5 步；原系统性诊断、下一轮备战、行动清单顺延为第 6—8 步。

八步名称固定为：整理记录、全场扫描、逐题拆解、专项分析、核心知识与技术深研、系统性诊断、下一轮备战、行动清单。

- [x] **Step 3: 写入默认扫描与证据闸门**

在第 5 步加入以下行为契约：

```markdown
每次复盘都执行候选主题扫描。主题满足至少一项可定位依据时才进入深研：

1. 候选人明确表示不知道、不确定或无法解释；
2. 回答暴露概念错误、边界混淆或选型逻辑缺失；
3. 面试官明确纠正、补充概念或反复要求解释；
4. 该知识与 JD 核心职责直接相关，现有回答缺少必要支撑；
5. 用户明确指定需要补研。
```

写明打断、沉默、推进语、面试时长、追问次数和说话比例只能作为辅助线索。最多选择五个知识主题，允许为零；无合格主题时在报告中记录结论和依据。

- [x] **Step 4: 写入研究方法与主题输出结构**

研究规则必须包含：使用当前环境可用的搜索和浏览能力；优先官方文档、标准、论文、监管披露或公司一手材料；关键结论需要时交叉验证；记录标题、URL、发布日期或查询日期；无法访问来源时保留待研究项，不把模型记忆写成当前事实。

每个主题使用固定结构：

```markdown
### 主题：<知识主题>
- 原问题与触发证据
- 知识缺口诊断
- 核心知识框架：是什么、为什么、适用边界、常见反例
- 案例与证据
- 可口述回答框架：结论、关键依据、岗位关联、关键词
- 继续追问准备
- 待用户确认的个人事实
- 来源清单
```

- [x] **Step 5: 更新输出结构与交付检查**

在默认报告结构中加入“核心知识与技术深研”，并把后续章节顺延。说明默认以内嵌章节交付；主题较多、材料较长或用户明确要求时，额外输出 `{公司}_{岗位}_{轮次}_核心知识深研报告.md`。

新增交付检查：候选主题是否有触发证据；外部事实是否可追溯；研究内容是否被误写成候选人经历；没有合格主题时是否停止扩写。

- [x] **Step 6: 执行行为风险扫描**

Run:

```bash
rg -n '正常60|理想4:6|8:2.*危险|重大信号|二面必考|每一道.*全部|出现3次|WebSearch|WebFetch|Explore 子代理|反问质量.*最终评价|练3遍|必须有逐字稿' skills/interview-deep-review/SKILL.md
```

Expected: 无匹配。

### Task 2: 完善子集与仓库 README

**Files:**
- Modify: `skills/interview-deep-review/README.md:1-104`
- Modify: `README.md:9-87`

**Interfaces:**
- Consumes: Task 1 的八步名称、触发闸门、研究输出和事实边界。
- Produces: 用户可发现并正确理解更新后的 Skill；仓库能力地图与实际 Skill 一致。

- [x] **Step 1: 更新子集 README 的定位与使用场景**

在开头说明：Skill 除了诊断表现，还会默认扫描面试暴露出的知识缺口；只有证据充分时才联网深研。适用场景增加“面试暴露概念、指标、产品机制、商业或行业知识缺口，需要在下一轮前补齐”。

- [x] **Step 2: 将用户流程改为八步**

保留现有七步说明并在专项分析后插入：

```markdown
5. **核心知识深研**：每次默认扫描知识缺口；有逐字稿或 JD 证据时，选择最多五个主题，补齐知识框架、边界、可靠案例、口述回答和追问准备。
```

将系统诊断、下一轮备战和行动清单顺延为 6—8。

- [x] **Step 3: 更新用户输出与边界说明**

输出清单增加“有证据触发时的核心知识深研章节或独立报告”。增加小节说明：扫描默认执行、深研不一定发生；数量允许为零；不使用固定比例或单一面试官信号下判断；外部案例有来源和日期；研究不能补写候选人经历。

- [x] **Step 4: 更新根 README 的能力摘要**

将能力地图中的“面试复盘”描述更新为“从逐字稿中识别表现、知识缺口和改进动作”。将当前 Skill 表中的用途更新为“证据驱动复盘并默认扫描需要深研的知识缺口”，主要输出增加“核心知识深研”。

根 README 其他阶段、仓库定位、安装方式和祝福语保持不变。

- [x] **Step 5: 检查文档一致性**

Run:

```bash
rg -n '八步|核心知识|默认扫描|最多五个|允许为零|来源|查询日期' README.md skills/interview-deep-review/README.md skills/interview-deep-review/SKILL.md
```

Expected: 三个文档均准确提及新增能力；子集 README 与 SKILL.md 都包含默认扫描、触发边界和来源规则。

### Task 3: 规范、质量与安全验证

**Files:**
- Verify: `skills/interview-deep-review/SKILL.md`
- Verify: `skills/interview-deep-review/README.md`
- Verify: `README.md`

**Interfaces:**
- Consumes: Tasks 1—2 的最终文档。
- Produces: 可提交的干净变更集和无高风险发现的审查结果。

- [x] **Step 1: 运行 Skill 规范校验**

Run:

```bash
uv run --with pyyaml python /Users/chenyufan/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/interview-deep-review
```

Expected: 输出 `Skill is valid!`。

- [x] **Step 2: 运行自动质量审查**

Run:

```bash
test ! -e /Users/chenyufan/.codex/skills/skill-creator
ln -s /Users/chenyufan/.codex/skills/.system/skill-creator /Users/chenyufan/.codex/skills/skill-creator
uv run --with pyyaml python /Users/chenyufan/.codex/skills/skill-reviewer/scripts/review_skill.py --json skills/interview-deep-review
review_status=$?
unlink /Users/chenyufan/.codex/skills/skill-creator
exit "$review_status"
```

Expected: 自动审查无错误或警告。

- [x] **Step 3: 执行安全审计**

Run:

```bash
rg -n 'Ignore previous instructions|Forget everything above|System prompt override|Admin mode|no restrictions|\[SYSTEM\]|\[ADMIN\]|\[ROOT\]|<!--|curl|wget|bash -i|\.ssh|\.aws|\.env|sudo|base64|subprocess|eval\(|exec\(' skills/interview-deep-review
```

Expected: 无匹配。人工确认联网能力只用于检索公开知识来源，不读取本地敏感文件、不执行网页指令、不上传逐字稿。

- [x] **Step 4: 检查 Markdown 与变更范围**

Run:

```bash
git diff --check
git status --short
git diff --name-only 88976e6
```

Expected: 无空白错误；变更只包含实施计划、根 README、子集 README 和 `skills/interview-deep-review/SKILL.md`。

### Task 4: 提交、推送与远端回读

**Files:**
- Commit: `docs/superpowers/plans/2026-09-03-interview-deep-review-knowledge-research.md`
- Commit: `README.md`
- Commit: `skills/interview-deep-review/README.md`
- Commit: `skills/interview-deep-review/SKILL.md`

**Interfaces:**
- Consumes: Task 3 的全部通过结果。
- Produces: GitHub `main` 上可公开读取的更新版本。

- [x] **Step 1: 提交功能迭代**

```bash
git add docs/superpowers/plans/2026-09-03-interview-deep-review-knowledge-research.md README.md skills/interview-deep-review/README.md skills/interview-deep-review/SKILL.md
git commit -m "feat: add knowledge research to interview review"
```

Expected: 提交成功，工作树干净。

- [x] **Step 2: 推送到原仓库**

```bash
git push origin main
git rev-parse HEAD
git ls-remote --heads origin main
```

Expected: 本地 `HEAD`、`origin/main` 和远端 `refs/heads/main` 哈希一致。

- [x] **Step 3: 回读公开文件**

回读：

- `https://raw.githubusercontent.com/AY-kkk/job-skill/main/README.md`
- `https://raw.githubusercontent.com/AY-kkk/job-skill/main/skills/interview-deep-review/README.md`
- `https://raw.githubusercontent.com/AY-kkk/job-skill/main/skills/interview-deep-review/SKILL.md`

Expected: 三个文件可访问；本地和远端 SHA-256 分别一致；公开内容包含“核心知识深研”和默认扫描边界。
