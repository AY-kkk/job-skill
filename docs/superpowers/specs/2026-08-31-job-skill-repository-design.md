# Job Skill 仓库首版设计

## 目标

把 `job-skill` 建设为中文优先、可持续扩展的求职 Skills 工具箱，并将 `interview-deep-review` 作为首个独立子 Skill 纳入仓库。

## 仓库结构

```text
job-skill/
├── README.md
└── skills/
    └── interview-deep-review/
        ├── README.md
        └── SKILL.md
```

- 根目录 `README.md`：说明仓库定位、适用人群、当前能力、目录约定和使用方式。
- `skills/interview-deep-review/README.md`：面向使用者介绍功能、输入、输出、工作流程、适用边界和安装方式。
- `skills/interview-deep-review/SKILL.md`：面向 Codex/Claude Code 等 Agent 的实际执行指令。

## 内容原则

1. 中文优先，保留必要的英文 Skill 名称与调用示例。
2. 仓库介绍不夸大能力；明确首版目前只包含面试深度复盘 Skill。
3. 压缩包内容仅作为原始素材。保留有效流程，但修正绝对化判断、缺少证据边界和依赖未声明等问题。
4. 深度复盘必须区分逐字稿事实、基于对话的推断和无法确认的信息。
5. 录音转写属于前置能力；没有可用转写工具时，应说明限制并请求逐字稿，不能假装已经完成转写。
6. 评分和面试官信号属于辅助判断，不包装成确定结论。

## 交付范围

本次包含：仓库中文介绍、Skill 中文介绍、规范化后的 Skill 文件、基础结构与 Markdown/Skill 校验。

本次不包含：新增其他求职 Skill、发布站点、自动安装脚本、包管理器分发或 CI/CD。

## 验收标准

- 新读者能从根 README 理解仓库是什么、目前有什么、如何使用。
- 用户能从子 Skill README 判断需要提供什么材料、会得到什么结果。
- `SKILL.md` 通过 Skill 结构校验，且没有未完成占位符。
- 仓库无压缩包、系统隐藏文件或无关产物。
- 改动提交并成功推送到 `AY-kkk/job-skill` 的 `main` 分支。
