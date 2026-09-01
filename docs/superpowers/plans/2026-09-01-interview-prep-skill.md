# Interview Prep Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `interview-prep` 完善并发布为面向产品、AI、商业化、运营等业务岗位的研究型面试准备 Skill。

**Architecture:** 根 README 先登记新能力；`skills/interview-prep/README.md` 面向使用者，`SKILL.md` 负责 Agent 路由，`WORKFLOW.md` 和 `prompts/` 承载详细研究方法；两个 Python 脚本作为可选辅助工具，并限制在公开网页和隔离依赖环境内运行。

**Tech Stack:** Markdown、YAML frontmatter、Python 3 标准库、requests、Beautiful Soup、Git

## Global Constraints

- 定位限定为产品、AI、商业化、运营等业务岗位的研究型面试准备。
- 先修改并提交根 `README.md`，再接入 Skill 子集。
- 不新增测试文件、测试套件、CI、锁文件、浏览器自动化或 Playwright 功能。
- 区分已验证事实、基于证据的推断、候选人观点和待确认信息。
- 不保留无评测依据的准确率、固定问题权重、固定耗时或“必考”承诺。
- 抓取脚本只访问公开 HTTP/HTTPS HTML 页面，并限制跳转和响应体大小。

---

### Task 1: 更新仓库主 README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: 已确认的新 Skill 定位。
- Produces: “面试准备”已收录状态和 `interview-prep` 子集入口。

- [ ] **Step 1: 更新能力地图和当前 Skill 表**

将“面试准备”状态改为“已收录首个 Skill”。在当前 Skill 表中加入：

```markdown
| [`interview-prep`](skills/interview-prep/) | 面向产品、AI、商业化、运营等业务岗位，完成岗位拆解、公司与产品研究、竞品分析、问题预测和回答准备 | JD、简历、目标公司与准备时间 | 岗位分析、研究材料、问题优先级、回答框架和行动清单 |
```

在安装示例中并列说明可复制 `interview-prep` 或 `interview-deep-review`，并在目录树中列出两个子集。

- [ ] **Step 2: 检查主 README 边界**

Run: `rg -n "interview-prep|产品、AI、商业化、运营|面试准备.*已收录" README.md`

Expected: 三类信息均能定位，且未把规划中的其他阶段标成已完成。

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add interview preparation skill to catalog"
```

### Task 2: 接入并完善 Skill 文档与 Prompt

**Files:**
- Create: `skills/interview-prep/README.md`
- Create: `skills/interview-prep/SKILL.md`
- Create: `skills/interview-prep/WORKFLOW.md`
- Create: `skills/interview-prep/prompts/README.md`
- Create: `skills/interview-prep/prompts/01_job_analysis.md`
- Create: `skills/interview-prep/prompts/02_product_extract.md`
- Create: `skills/interview-prep/prompts/03_competitor_discovery.md`
- Create: `skills/interview-prep/prompts/04_comparison.md`
- Create: `skills/interview-prep/prompts/05_swot.md`
- Create: `skills/interview-prep/prompts/06_question_prediction.md`
- Create: `skills/interview-prep/prompts/07_answer_generation.md`
- Create: `skills/interview-prep/prompts/08_industry_insight.md`

**Interfaces:**
- Consumes: 压缩包中对应文件，仅作为原始素材。
- Produces: 用户介绍、Agent 路由、三种准备模式、六步研究工作流和八个可复用模板。

- [ ] **Step 1: 编写用户 README**

说明 Skill 适用岗位、三种输入层级、快速/标准/专项模式、主要输出、事实边界、隐私提醒、安装与调用示例。明确问题预测是准备优先级，不是真题预测承诺。

- [ ] **Step 2: 精简并规范 SKILL.md**

frontmatter 使用：

```yaml
---
name: interview-prep
description: 为产品、AI、商业化、运营等业务岗位生成证据驱动的研究型面试准备方案。用于用户需要拆解 JD、研究目标公司与产品、分析竞品、确定问题优先级、打磨真实回答或准备行业观点；不用于纯技术岗位题库、简历改写或面试后复盘。
---
```

正文保留输入确认、模式选择、六步路由、事实规则、回答真实性和交付检查。详细执行步骤指向 `WORKFLOW.md`，模板按需指向 `prompts/01—08`，不重复整套技术架构和文件树。

- [ ] **Step 3: 修订 WORKFLOW.md**

保留六步工作流，增加每一步的输入、证据来源、停止条件和输出。将固定年份搜索词改为“当前年份”，删除固定耗时；新增快速模式、标准模式、专项模式的选择条件。网页不可访问时允许用户提供页面文本。

- [ ] **Step 4: 修订八个 Prompt**

统一增加以下约束：

```markdown
- 已验证事实必须能回溯到输入或来源 URL，并保留查询日期。
- 推断、观点和待确认信息单独标注。
- 不使用用户未确认的经历、数字或个人贡献。
- 缺少材料时输出澄清问题，不补写事实。
```

`01_job_analysis.md` 将岗位级别、汇报对象和面试轮次标为推断；`03_competitor_discovery.md` 不依赖模型记忆生成 URL；`04_comparison.md` 不用 ✓/✗ 表示未验证能力；`05_swot.md` 区分内外部证据；`06_question_prediction.md` 删除固定权重和“100% 必考”；`07_answer_generation.md` 不强制编造量化成果；`08_industry_insight.md` 删除“金句”式确定性预测，保留可口述观点及反方证据。

- [ ] **Step 5: 校验文档引用**

Run: `rg -n "WORKFLOW.md|prompts/0[1-8]_" skills/interview-prep/SKILL.md skills/interview-prep/WORKFLOW.md`

Expected: 主流程和八个模板均可从入口文档定位。

### Task 3: 接入并加固辅助脚本

**Files:**
- Create: `skills/interview-prep/scripts/README.md`
- Create: `skills/interview-prep/scripts/product_extractor.py`
- Create: `skills/interview-prep/scripts/product_scraper.py`

**Interfaces:**
- Consumes: 页面文本或用户指定的公开产品页 URL。
- Produces: JSON 或 Markdown 产品信息；失败时返回清晰错误，不访问内网目标。

- [ ] **Step 1: 保留规则提取器并改善 CLI 错误**

保留 `ProductInfo`、`clean_text()`、`extract_product_info()`、`save_json()` 和 `save_markdown()`。捕获 `OSError`、`UnicodeError`、`json.JSONDecodeError`、`TypeError` 与 `KeyError`，向标准错误输出 `错误：<原因>` 并返回退出码 1；成功返回 0。

- [ ] **Step 2: 为抓取器增加公开 URL 校验**

新增：

```python
MAX_REDIRECTS = 5
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = ("text/html", "application/xhtml+xml")

def validate_public_url(url: str) -> str:
    """返回规范 URL；拒绝非 HTTP(S)、凭据、无主机及非公网解析地址。"""

def resolve_public_addresses(hostname: str) -> list[str]:
    """解析主机并要求每个地址的 ipaddress.ip_address(address).is_global 为真。"""
```

使用 `socket.getaddrinfo()` 和 `ipaddress.ip_address()`；拒绝 localhost、环回、私有、链路本地、保留和未指定地址。

- [ ] **Step 3: 限制跳转、类型和响应体**

将 `fetch_page()` 改为 `requests.Session().get(..., allow_redirects=False, stream=True)`；每个跳转目标重新调用 `validate_public_url()`，最多五次；只接受允许的 HTML Content-Type；逐块读取并在超过 5 MiB 时停止。保持 TLS 验证开启，移除 Google Referer。

- [ ] **Step 4: 修订脚本说明**

用以下隔离安装方式替换全局安装：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install requests beautifulsoup4
```

同时提供 `uv run --with requests --with beautifulsoup4 ...` 示例。说明抓取前应确认网站条款与 robots 规则；移除未实现的 Playwright 依赖。

- [ ] **Step 5: 运行非抓取式检查**

Run: `python3 -m py_compile skills/interview-prep/scripts/product_extractor.py skills/interview-prep/scripts/product_scraper.py`

Run: `python3 skills/interview-prep/scripts/product_extractor.py --help >/dev/null`

Run: `uv run --with requests --with beautifulsoup4 python skills/interview-prep/scripts/product_scraper.py --help >/dev/null`

Expected: 三条命令退出码均为 0；不访问真实网站。

- [ ] **Step 6: Commit Skill 子集**

```bash
git add skills/interview-prep
git commit -m "feat: add research-driven interview prep skill"
```

### Task 4: 发布前审查与推送

**Files:**
- Verify: `README.md`
- Verify: `skills/interview-prep/`

**Interfaces:**
- Consumes: 前三项任务的全部交付物。
- Produces: 通过结构与安全检查、公开可回读的 GitHub `main`。

- [ ] **Step 1: 运行 Skill 校验和审查器**

Run canonical validator with PyYAML through `uv`; run `skill-reviewer` with its validator path temporarily redirected to `.system/skill-creator/scripts/quick_validate.py`.

Expected: canonical validator reports `Skill is valid!`; reviewer has no errors or warnings。

- [ ] **Step 2: 运行静态安全检查**

检查提示注入、硬编码用户路径、凭据、`--break-system-packages`、伪造 Referer、禁用 TLS、`subprocess`、`eval` 和 `exec`。Expected: 无危险命中；合理的 `requests` 网络调用只存在于 `product_scraper.py`。

- [ ] **Step 3: 检查仓库状态**

Run: `git diff --check && git status --short --branch && find skills/interview-prep -type f -print | sort`

Expected: 工作树干净；目录只包含约定的文档、八个 Prompt 和两个脚本。

- [ ] **Step 4: 推送并回读**

```bash
git push origin main
git ls-remote --heads origin main
```

从公开 raw URL 回读根 README、Skill README 和 `SKILL.md`。Expected: 远端哈希与本地 `HEAD` 一致，三个文件内容可访问。
