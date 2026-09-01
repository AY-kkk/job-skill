#!/usr/bin/env python3
"""
产品信息结构化提取器 (Product Info Extractor)

用途：
    从产品页面的纯文本中，智能提取产品名称、定位、核心功能、核心优势、
    应用场景、定价模式、技术架构等结构化信息。

设计原则：
    1. 只负责"文本 → 结构化数据"的提取，不负责网页获取
    2. 输入可以是浏览工具取得的页面文本、手动粘贴的文本或本地文件
    3. 输出 JSON 或 Markdown

使用方式：
    # 从文本文件提取
    python3 product_extractor.py --input page.txt --output product.json

    # 从标准输入管道提取（配合其他工具）
    cat page.txt | python3 product_extractor.py --stdin --output product.json

    # 多产品批量（JSON数组输入）
    python3 product_extractor.py --batch products_texts.json --output report.md --format md
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# ---------------------------------------------------------------------------
# 配置：关键词与提取规则
# ---------------------------------------------------------------------------

# 各区块的关键词（按优先级排序，越靠前权重越高）
SECTION_PATTERNS = {
    "core_features": [
        # 中文
        r"核心功能", r"产品功能", r"功能模块", r"产品能力", r"核心能力",
        r"功能介绍", r"能力介绍", r"功能亮点", r"主要功能",
        r"功能\s*[:：]", r"能力\s*[:：]",
        # 英文
        r"Features", r"Capabilities", r"Core Features", r"Key Features",
        r"Product Features", r"What it does",
    ],
    "core_advantages": [
        r"核心优势", r"产品优势", r"核心亮点", r"产品亮点",
        r"为什么选择", r"为什么用", r"优势特性", r"竞争优势",
        r"优势\s*[:：]", r"亮点\s*[:：]", r"价值\s*[:：]",
        r"Advantages", r"Benefits", r"Why", r"Key Benefits",
        r"Core Advantages", r"Product Advantages",
    ],
    "use_cases": [
        r"应用场景", r"使用场景", r"适用场景", r"典型场景",
        r"场景介绍", r"业务场景", r"解决方案",
        r"场景\s*[:：]", r"应用\s*[:：]",
        r"Use Cases", r"Scenarios", r"Applications",
        r"Typical Scenarios", r"Application Scenarios",
    ],
    "pricing": [
        r"定价", r"价格", r"计费", r"收费", r"费用",
        r"价格方案", r"计费模式", r"定价模式", r"购买方式",
        r"Pricing", r"Price", r"Cost", r"Plans",
        r"计费方式", r"收费模式", r"套餐",
    ],
    "architecture": [
        r"产品架构", r"技术架构", r"总体架构", r"架构设计",
        r"架构图", r"技术原理", r"产品原理",
        r"Architecture", r"Technical Architecture", r"System Architecture",
        r"产品体系", r"整体架构",
    ],
    "customers": [
        r"客户案例", r"标杆案例", r"成功案例", r"客户故事",
        r"合作客户", r"典型客户", r"客户",
        r"Customers", r"Case Studies", r"Success Stories",
        r"客户名单", r"代表客户",
    ],
}

# 需要过滤的噪音模式（匹配到就丢弃这行）
NOISE_PATTERNS = [
    r"^第[一二三四五六七八九十\d]+[篇章节节]",  # 章节导航
    r"下一篇", r"上一篇", r"相关文档", r"相关文章",
    r"该文章对您有帮助吗", r"有帮助", r"没帮助",
    r"©.*版权", r"版权所有", r"备案号",
    r"隐私政策", r"服务条款", r"用户协议",
    r"联系我们", r"关于我们", r"加入我们",
    r"意见反馈", r"产品反馈",
    r"扫码关注", r"微信公众号",
    r"^\d+$",  # 纯数字行
    r"^[a-zA-Z0-9_\-]{20,}$",  # 长串ID/Token
    r"返回顶部", r"跳转到",
    r"加载中", r"Loading",
    r"页面.*时间", r"更新时间",
    r"编辑", r"审核", r"发布",
]

# 典型"条目"句式特征（一个功能/优势/场景通常是这种结构）
ITEM_PATTERNS = [
    r"^[\d]+[.、)）]\s*.+",  # "1. xxx" 或 "1、xxx"
    r"^[-•●○◆■▪▫–—]\s*.+",  # 列表符号开头
    r"^[一二三四五六七八九十]+[.、)）]\s*.+",  # 中文序号
    r"^[（(][一二三四五六七八九十\d]+[)）]\s*.+",  # "(1) xxx" 或 "（一）xxx"
]

# 描述性句子关键词（更可能是功能/优势描述）
DESCRIPTIVE_KEYWORDS = [
    "支持", "提供", "实现", "帮助", "助力", "打造", "构建",
    "具备", "拥有", "覆盖", "满足", "解决", "提升", "降低",
    "自动", "智能", "一键", "全流程", "一站式",
    "可", "能够", "可以", "适用于", "面向",
    "support", "provide", "enable", "help", "build",
    "deliver", "offer", "allow",
]


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class ProductInfo:
    """单个产品的结构化信息"""
    name: str = ""
    url: str = ""
    company: str = ""
    positioning: str = ""
    core_features: List[str] = field(default_factory=list)
    core_advantages: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    pricing: str = ""
    architecture: str = ""
    customers: List[str] = field(default_factory=list)
    extraction_notes: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 文本清理
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    清理原始文本：去重、去噪音、规范格式
    """
    lines = text.split("\n")
    cleaned = []
    seen = set()

    for line in lines:
        line = line.strip()

        # 空行跳过
        if not line:
            continue

        # 去重
        if line in seen:
            continue
        seen.add(line)

        # 过滤噪音
        is_noise = False
        for pattern in NOISE_PATTERNS:
            if re.search(pattern, line):
                is_noise = True
                break
        if is_noise:
            continue

        # 太短的跳过（小于3个字符）
        if len(line) < 3:
            continue

        # 纯标点/符号跳过
        if re.match(r'^[^\w\u4e00-\u9fff]+$', line):
            continue

        cleaned.append(line)

    return "\n".join(cleaned)


# ---------------------------------------------------------------------------
# 区块定位与提取
# ---------------------------------------------------------------------------

def find_section_boundaries(lines: List[str], pattern: str) -> List[int]:
    """
    在文本行中找到匹配某个关键词模式的行号（作为区块标题位置）
    """
    matches = []
    for i, line in enumerate(lines):
        if re.search(pattern, line, re.IGNORECASE):
            # 标题行通常比较短
            if len(line) < 60:
                matches.append(i)
    return matches


def extract_section_items(lines: List[str], section_patterns: List[str], max_items: int = 12) -> List[str]:
    """
    从文本行中提取某个区块的条目列表。

    策略：
    1. 找到所有可能的区块标题行
    2. 对每个标题，向后扫描提取条目（直到下一个标题或30行后）
    3. 条目判定：列表样式行 + 描述性关键词行
    """
    all_items = []

    for pattern in section_patterns:
        starts = find_section_boundaries(lines, pattern)

        for start in starts:
            # 确定区块结束位置
            end_idx = min(start + 30, len(lines))

            # 找下一个可能的标题行（比start行短，像标题）
            for j in range(start + 2, min(start + 30, len(lines))):
                next_line = lines[j].strip()
                # 短行 + 不含句号/逗号 + 不是列表项 → 可能是下一个区块标题
                if (len(next_line) < 25
                    and not next_line.endswith(("。", "，", ",", ".", "：", ":"))
                    and not any(next_line.startswith(sym) for sym in ["-", "•", "●", "1.", "2.", "（1）"])):
                    end_idx = j
                    break

            # 提取区块内的条目
            section_lines = lines[start + 1:end_idx]

            for line in section_lines:
                line = line.strip()

                # 过滤太长的段落（超过100字的大概率是段落描述，不是条目）
                if len(line) > 100:
                    continue

                # 条件1：明确的列表格式
                is_list_item = any(re.match(p, line) for p in ITEM_PATTERNS)

                # 条件2：包含描述性关键词，且长度合适
                is_descriptive = (
                    5 <= len(line) <= 80
                    and any(kw in line for kw in DESCRIPTIVE_KEYWORDS)
                )

                if is_list_item or is_descriptive:
                    # 清理列表前缀符号
                    cleaned_line = re.sub(r'^[\d]+[.、)）]\s*', '', line)
                    cleaned_line = re.sub(r'^[-•●○◆■▪▫–—]\s*', '', cleaned_line)
                    cleaned_line = re.sub(r'^[一二三四五六七八九十]+[.、)）]\s*', '', cleaned_line)
                    cleaned_line = re.sub(r'^[（(][一二三四五六七八九十\d]+[)）]\s*', '', cleaned_line)
                    cleaned_line = cleaned_line.strip()

                    if len(cleaned_line) >= 4:
                        all_items.append(cleaned_line)

    # 去重（保持顺序）
    seen = set()
    unique_items = []
    for item in all_items:
        # 规范化比较（去空格、转小写）
        norm = re.sub(r'\s+', '', item).lower()
        if norm not in seen:
            seen.add(norm)
            unique_items.append(item)

    return unique_items[:max_items]


def extract_positioning(lines: List[str], product_name: str = "") -> str:
    """
    提取产品定位/一句话描述。
    策略：找页面前30行中，最像"产品定位"的那句话
    """
    # 候选行：前30行中长度15-80字，包含描述性关键词的句子
    candidates = []
    for i, line in enumerate(lines[:40]):
        line = line.strip()
        if 15 <= len(line) <= 100:
            score = 0
            # 包含定位关键词加分
            if any(kw in line for kw in ["新一代", "致力于", "面向", "打造", "提供", "帮助", "助力", "一站式", "全流程"]):
                score += 2
            # 包含产品名加分
            if product_name and product_name in line:
                score += 3
            # 有句号结尾的完整句子加分
            if line.endswith("。"):
                score += 1
            # 越靠前分越高
            score += max(0, 10 - i) * 0.1

            if score > 0:
                candidates.append((score, line))

    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]

    return ""


# ---------------------------------------------------------------------------
# 主提取流程
# ---------------------------------------------------------------------------

def extract_product_info(
    raw_text: str,
    product_name: str = "",
    company: str = "",
    url: str = "",
) -> ProductInfo:
    """
    从产品页面纯文本中提取结构化产品信息
    """
    info = ProductInfo(name=product_name, company=company, url=url)

    # 1. 清理文本
    cleaned = clean_text(raw_text)
    lines = cleaned.split("\n")

    if len(lines) < 3:
        info.extraction_notes.append("文本内容过少，可能提取失败")
        return info

    # 2. 提取产品名称（如果没提供）
    if not info.name:
        # 找第一个h1样式的行（短文本、有产品特征词）
        for line in lines[:15]:
            if 2 <= len(line) <= 30 and any(kw in line for kw in ["Agent", "平台", "系统", "产品", "服务"]):
                info.name = line
                break
        if not info.name and lines:
            info.name = lines[0][:30]

    # 3. 产品定位
    info.positioning = extract_positioning(lines, info.name)

    # 4. 核心功能
    info.core_features = extract_section_items(lines, SECTION_PATTERNS["core_features"])

    # 5. 核心优势
    info.core_advantages = extract_section_items(lines, SECTION_PATTERNS["core_advantages"])

    # 6. 应用场景
    info.use_cases = extract_section_items(lines, SECTION_PATTERNS["use_cases"])

    # 7. 定价
    pricing_items = extract_section_items(lines, SECTION_PATTERNS["pricing"], max_items=8)
    info.pricing = "\n".join(pricing_items) if pricing_items else ""

    # 8. 架构
    arch_items = extract_section_items(lines, SECTION_PATTERNS["architecture"], max_items=10)
    info.architecture = "\n".join(arch_items) if arch_items else ""

    # 9. 客户
    info.customers = extract_section_items(lines, SECTION_PATTERNS["customers"], max_items=10)

    # 10. 提取质量评估
    extracted_count = sum([
        bool(info.positioning),
        bool(info.core_features),
        bool(info.core_advantages),
        bool(info.use_cases),
    ])
    info.extraction_notes.append(f"结构化提取: {extracted_count}/4 字段")
    info.extraction_notes.append(f"文本总行数: {len(lines)}")

    return info


# ---------------------------------------------------------------------------
# 输出格式
# ---------------------------------------------------------------------------

def save_json(products: List[ProductInfo], output_path: str):
    """保存为 JSON"""
    data = [asdict(p) for p in products]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON 已保存: {output_path}")


def save_markdown(products: List[ProductInfo], output_path: str, title: str = "竞品分析报告"):
    """保存为 Markdown 报告"""
    lines_md = [f"# {title}", ""]

    # 概览表
    lines_md.append("## 产品概览")
    lines_md.append("")
    lines_md.append("| 产品 | 公司 | 一句话定位 | 功能数 | 优势数 | 场景数 |")
    lines_md.append("|------|------|-----------|-------|-------|-------|")
    for p in products:
        pos = p.positioning[:40] + "..." if len(p.positioning) > 40 else (p.positioning or "—")
        lines_md.append(f"| {p.name or '—'} | {p.company or '—'} | {pos} | {len(p.core_features)} | {len(p.core_advantages)} | {len(p.use_cases)} |")
    lines_md.append("")

    # 对比表（功能/优势横向对比）
    if len(products) >= 2:
        lines_md.append("## 核心能力对比")
        lines_md.append("")
        lines_md.append("### 核心功能对比")
        lines_md.append("")
        lines_md.append("| 维度 | " + " | ".join(p.name or f"产品{i+1}" for i, p in enumerate(products)) + " |")
        lines_md.append("|------|" + "|".join(["------"] * len(products)) + "|")

        # 合并所有产品的功能关键词，逐行对比
        all_features = []
        seen_feat = set()
        for p in products:
            for f in p.core_features:
                key = f[:20]  # 用前20字去重
                if key not in seen_feat:
                    seen_feat.add(key)
                    all_features.append(f)

        # 取前10个最有代表性的
        for feat in all_features[:10]:
            row = [feat[:20]]
            for p in products:
                has = "✓" if any(feat[:10] in f for f in p.core_features) else "—"
                row.append(has)
            lines_md.append("| " + " | ".join(row) + " |")

        lines_md.append("")

    # 每个产品详情
    lines_md.append("## 产品详情")
    lines_md.append("")

    for i, p in enumerate(products, 1):
        lines_md.append(f"### {i}. {p.name or f'产品{i}'}")
        lines_md.append("")
        lines_md.append(f"- **所属公司**：{p.company or '—'}")
        if p.url:
            lines_md.append(f"- **产品链接**：[{p.url}]({p.url})")
        lines_md.append("")

        if p.positioning:
            lines_md.append("**产品定位**")
            lines_md.append("")
            lines_md.append(f"> {p.positioning}")
            lines_md.append("")

        if p.core_features:
            lines_md.append("**核心功能/能力**")
            lines_md.append("")
            for f in p.core_features:
                lines_md.append(f"- {f}")
            lines_md.append("")

        if p.core_advantages:
            lines_md.append("**核心优势**")
            lines_md.append("")
            for a in p.core_advantages:
                lines_md.append(f"- {a}")
            lines_md.append("")

        if p.use_cases:
            lines_md.append("**应用场景**")
            lines_md.append("")
            for uc in p.use_cases:
                lines_md.append(f"- {uc}")
            lines_md.append("")

        if p.pricing:
            lines_md.append("**定价模式**")
            lines_md.append("")
            lines_md.append(p.pricing)
            lines_md.append("")

        if p.architecture:
            lines_md.append("**产品架构**")
            lines_md.append("")
            lines_md.append(p.architecture)
            lines_md.append("")

        if p.customers:
            lines_md.append("**客户案例**")
            lines_md.append("")
            for c in p.customers:
                lines_md.append(f"- {c}")
            lines_md.append("")

        lines_md.append("---")
        lines_md.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_md))
    print(f"✅ Markdown 报告已保存: {output_path}")


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="产品信息结构化提取器 - 从页面纯文本中提取功能/优势/场景等信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单文件提取
  python3 product_extractor.py --input page.txt --name "产品名" --company "公司名"

  # 管道输入（页面文本已保存为 page.txt）
  python3 product_extractor.py --stdin --output product.json < page.txt

  # 批量处理（JSON数组，每个元素含 text/name/company/url）
  python3 product_extractor.py --batch input.json --output report.md --format md
        """
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input", "-i", type=str, help="输入文本文件路径")
    input_group.add_argument("--stdin", action="store_true", help="从标准输入读取文本")
    input_group.add_argument("--batch", type=str, help="批量JSON文件路径")

    parser.add_argument("--output", "-o", type=str, default="output.json",
                        help="输出文件路径")
    parser.add_argument("--format", "-f", type=str, choices=["json", "md"], default="json",
                        help="输出格式: json / md")
    parser.add_argument("--name", type=str, default="", help="产品名称（单文件模式）")
    parser.add_argument("--company", type=str, default="", help="公司名称（单文件模式）")
    parser.add_argument("--url", type=str, default="", help="产品URL（单文件模式）")
    parser.add_argument("--title", type=str, default="竞品分析报告",
                        help="Markdown报告标题")

    args = parser.parse_args()

    try:
        products = []

        if args.batch:
            with open(args.batch, "r", encoding="utf-8") as f:
                batch_data = json.load(f)
            if not isinstance(batch_data, list):
                raise TypeError("批量输入必须是 JSON 数组")

            for index, item in enumerate(batch_data, 1):
                if not isinstance(item, dict):
                    raise TypeError(f"批量输入第 {index} 项必须是 JSON 对象")
                info = extract_product_info(
                    raw_text=item.get("text", ""),
                    product_name=item.get("name", ""),
                    company=item.get("company", ""),
                    url=item.get("url", ""),
                )
                products.append(info)

        else:
            if args.stdin:
                raw_text = sys.stdin.read()
            else:
                with open(args.input, "r", encoding="utf-8") as f:
                    raw_text = f.read()

            info = extract_product_info(
                raw_text=raw_text,
                product_name=args.name,
                company=args.company,
                url=args.url,
            )
            products.append(info)

        if args.format == "json":
            save_json(products, args.output)
        else:
            save_markdown(products, args.output, args.title)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, KeyError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(f"\n📊 提取完成: {len(products)} 个产品")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
