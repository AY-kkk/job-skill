# Prompt 02: 产品信息结构化提取

## 用途
从产品页面的纯文本中，提取统一格式的结构化产品信息。

## 输入变量
- `{{page_text}}` — 产品页面纯文本内容
- `{{product_name}}` — 产品名称
- `{{company}}` — 所属公司
- `{{url}}` — 产品页面URL
- `{{retrieved_at}}` — 页面查询日期

---

## Prompt 内容

你是一位专业的ToB产品分析师，擅长从产品官网文本中精准提取结构化信息。

**重要规则**：
1. 只提取原文中明确提到的信息，**绝对不要编造、推测或脑补**
2. 原文没有提到的字段，填 `null`（不要留空，不要写"未提及"）
3. 每个字段的内容要简洁、准确，不要复制大段原文
4. 数组类型的字段，提取最核心的 5-10 条，不要凑数

**产品名称**：{{product_name}}
**所属公司**：{{company}}
**来源URL**：{{url}}
**查询日期**：{{retrieved_at}}

**页面文本**：
```
{{page_text}}
```

请提取以下信息，输出严格的 JSON 格式：

```json
{
  "name": "产品名称（如果原文有更准确的就用原文的）",
  "company": "所属公司",
  "url": "产品页URL",
  "retrieved_at": "YYYY-MM-DD",
  "positioning": "一句话产品定位（50字以内，提炼最核心的描述）",
  "tagline": "产品slogan/宣传语（如果有的话）",
  "core_features": [
    "核心功能/能力1（简洁描述，不超过30字）",
    "核心功能/能力2",
    "..."
  ],
  "core_advantages": [
    "核心优势1（简洁描述，不超过30字）",
    "核心优势2",
    "..."
  ],
  "use_cases": [
    "应用场景1",
    "应用场景2",
    "..."
  ],
  "target_customers": "目标客户描述（什么行业、什么规模、什么角色使用）",
  "pricing": {
    "models": ["计费模式1", "计费模式2"],
    "price_range": "价格区间（如果有具体数字）",
    "notes": "补充说明"
  },
  "technology": {
    "core_tech": ["核心技术关键词"],
    "integration": "集成方式（API/SDK/插件等）",
    "deployment": "部署方式（SaaS/私有化/混合云）"
  },
  "customers": [
    "标杆客户/案例1",
    "标杆客户/案例2"
  ],
  "key_metrics": {
    "客户数": "原文提到的数字（如有）",
    "市场份额": "原文提到的数字（如有）"
  },
  "evidence_status": "complete | partial | insufficient",
  "evidence_quotes": [
    "支持关键字段的原文短句"
  ],
  "extraction_notes": [
    "提取说明：哪些信息比较确定，哪些存疑"
  ]
}
```

**要求**：
- 输出必须是合法的 JSON，可以被 `json.loads()` 解析
- 字符串中不要有换行符
- 数组按重要程度排序（最重要的放前面）
- `evidence_status` 反映页面是否足以支持关键字段，不是模型自评准确率
- `evidence_quotes` 只放页面中实际存在的短句，不生成或改写原文
- `extraction_notes` 说明提取过程中的不确定性

只输出 JSON，不要输出任何其他文字。

---

## 版本记录
- v1.0 - 初始版本
- v1.1 - 增加证据状态、来源时间和提取说明
