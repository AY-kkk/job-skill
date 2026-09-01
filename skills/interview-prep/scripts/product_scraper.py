#!/usr/bin/env python3
"""
产品信息深度采集器 (Product Info Scraper)

用途：
    从指定的产品官网URL中，结构化提取产品名称、定位、核心功能、
    核心优势、应用场景、定价模式、技术架构等信息，用于面试竞品分析。

使用方式：
    python3 product_scraper.py --urls "url1,url2,url3" --output output.json
    python3 product_scraper.py --config config.json --output output.md

支持模式：
    1. URL列表模式：直接传一组URL，自动提取并输出结构化JSON
    2. 配置文件模式：通过JSON配置指定公司+产品+URL，输出Markdown报告
"""

import argparse
import ipaddress
import json
import re
import socket
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

USER_AGENTS = [
    "job-skill-interview-prep/1.0 (+https://github.com/AY-kkk/job-skill)",
]

REQUEST_DELAY = 1.5  # 请求间隔（秒），避免被封
REQUEST_TIMEOUT = 15  # 超时时间（秒）
MAX_REDIRECTS = 5
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = ("text/html", "application/xhtml+xml")

# 常见"核心功能/优势/场景"等区块的关键词（中英文）
SECTION_KEYWORDS = {
    "product_name": ["产品名称", "产品", "Product", ""],
    "positioning": ["产品定位", "定位", "是什么", "Positioning", "What is", "概述", "简介", "产品简介"],
    "core_features": ["核心功能", "产品能力", "功能", "功能模块", "产品功能", "Features", "Capabilities", "核心能力", "四大能力"],
    "core_advantages": ["核心优势", "产品优势", "优势", "为什么选择", "Advantages", "Benefits", "Why", "亮点", "三大优势", "四大优势"],
    "use_cases": ["应用场景", "使用场景", "场景", "适用场景", "Use Cases", "Scenarios", "典型场景"],
    "pricing": ["定价", "价格", "计费", "Pricing", "费用", "收费模式", "购买"],
    "architecture": ["产品架构", "技术架构", "架构", "Architecture", "技术原理", "总体架构"],
    "customers": ["客户案例", "标杆案例", "客户", "Customers", "案例", "合作客户"],
}


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class ProductInfo:
    """单个产品的结构化信息"""
    name: str = ""
    url: str = ""
    company: str = ""
    positioning: str = ""  # 一句话定位
    core_features: List[str] = field(default_factory=list)
    core_advantages: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    pricing: str = ""
    architecture: str = ""
    customers: List[str] = field(default_factory=list)
    raw_text: str = ""  # 原始页面文本（兜底用）
    extraction_notes: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 网页获取
# ---------------------------------------------------------------------------

def resolve_public_addresses(hostname: str) -> List[str]:
    """解析主机名，并拒绝任何非公网地址。"""
    try:
        address_info = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"域名无法解析：{hostname}") from exc

    addresses = sorted({item[4][0].split("%", 1)[0] for item in address_info})
    if not addresses:
        raise ValueError(f"域名没有可用地址：{hostname}")

    for address in addresses:
        try:
            parsed_address = ipaddress.ip_address(address)
        except ValueError as exc:
            raise ValueError(f"无法识别解析地址：{address}") from exc
        if not parsed_address.is_global:
            raise ValueError(f"拒绝访问非公网地址：{address}")

    return addresses


def validate_public_url(url: str) -> str:
    """返回经校验的公开 HTTP(S) URL。"""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL 不能为空")

    normalized = url.strip()
    parsed = urlparse(normalized)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("只允许 http 或 https URL")
    if parsed.username or parsed.password:
        raise ValueError("URL 不得包含用户名或密码")
    if not parsed.hostname:
        raise ValueError("URL 缺少有效主机名")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("URL 端口无效") from exc

    resolve_public_addresses(parsed.hostname)
    return normalized


def fetch_page(url: str) -> Optional[str]:
    """
    获取网页HTML内容
    返回 HTML 字符串，失败返回 None
    """
    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    session = requests.Session()
    session.headers.update(headers)
    try:
        current_url = validate_public_url(url)
        for redirect_count in range(MAX_REDIRECTS + 1):
            with session.get(
                current_url,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
                stream=True,
            ) as response:
                if response.is_redirect or response.is_permanent_redirect:
                    location = response.headers.get("Location")
                    if not location:
                        raise ValueError("跳转响应缺少 Location")
                    if redirect_count >= MAX_REDIRECTS:
                        raise ValueError(f"跳转次数超过 {MAX_REDIRECTS} 次")
                    current_url = validate_public_url(urljoin(current_url, location))
                    continue

                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").lower()
                if not any(content_type.startswith(item) for item in ALLOWED_CONTENT_TYPES):
                    raise ValueError(f"只接受 HTML 页面，实际类型：{content_type or '未知'}")

                content_length = response.headers.get("Content-Length")
                if content_length:
                    try:
                        declared_length = int(content_length)
                    except ValueError:
                        declared_length = None
                    if declared_length is not None and declared_length > MAX_RESPONSE_BYTES:
                        raise ValueError("页面响应超过 5 MiB 限制")

                body = bytearray()
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    body.extend(chunk)
                    if len(body) > MAX_RESPONSE_BYTES:
                        raise ValueError("页面响应超过 5 MiB 限制")

                encoding = response.encoding
                if not encoding or encoding.lower() == "iso-8859-1":
                    encoding = response.apparent_encoding or "utf-8"
                return bytes(body).decode(encoding, errors="replace")

        raise ValueError(f"跳转次数超过 {MAX_REDIRECTS} 次")
    except (requests.exceptions.RequestException, ValueError) as exc:
        print(f"  ⚠️  获取失败: {url} - {exc}", file=sys.stderr)
        return None
    finally:
        session.close()


# ---------------------------------------------------------------------------
# 文本提取
# ---------------------------------------------------------------------------

def extract_text_from_html(html: str) -> str:
    """从HTML中提取纯净文本（去掉script/style/nav等）"""
    soup = BeautifulSoup(html, "html.parser")

    # 移除无用标签
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "iframe"]):
        tag.decompose()

    # 获取文本
    text = soup.get_text(separator="\n", strip=True)

    # 清理多余空行
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def extract_title(html: str) -> str:
    """提取页面标题"""
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True)
    return ""


def extract_meta_description(html: str) -> str:
    """提取 meta description（通常是产品一句话定位）"""
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    meta_og = soup.find("meta", attrs={"property": "og:description"})
    if meta_og and meta_og.get("content"):
        return meta_og["content"].strip()
    return ""


def extract_h1(html: str) -> str:
    """提取页面h1标题"""
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return ""


# ---------------------------------------------------------------------------
# 结构化信息提取
# ---------------------------------------------------------------------------

def extract_section_items(text: str, section_keywords: List[str]) -> List[str]:
    """
    从页面文本中，根据关键词定位某个区块，并提取该区块的条目列表。
    适用于：核心功能、核心优势、应用场景等列表型内容。

    思路：
    1. 找到包含关键词的行（作为区块标题）
    2. 提取该标题之后、下一个大标题之前的所有内容
    3. 从内容中识别列表项（短句、有编号的、特征句式的）
    """
    lines = text.split("\n")
    items = []

    # 先找到所有可能的区块起始行
    section_starts = []
    for i, line in enumerate(lines):
        for keyword in section_keywords:
            if keyword and keyword in line and len(line) < 50:
                section_starts.append(i)
                break

    if not section_starts:
        return []

    # 对每个区块起始位置，提取后续内容直到下一个大标题
    for start_idx in section_starts:
        # 找区块结束位置（下一个短行标题，或20行后）
        end_idx = min(start_idx + 30, len(lines))
        for j in range(start_idx + 1, min(start_idx + 30, len(lines))):
            line = lines[j].strip()
            # 短行且像标题的（行短、不含句号），可能是下一个区块
            if 1 < len(line) < 20 and not line.endswith(("。", "，", ",", ".", "：", ":")) and j > start_idx + 3:
                end_idx = j
                break

        # 提取区块内的条目
        section_lines = lines[start_idx + 1:end_idx]

        for line in section_lines:
            line = line.strip()
            # 过滤太短或太长的
            if len(line) < 3 or len(line) > 100:
                continue
            # 过滤纯标点或纯数字
            if re.match(r'^[\d\s\W]+$', line):
                continue
            # 跳过明显的导航或版权信息
            if any(skip in line for skip in ["©", "备案", "隐私", "条款", "联系我们", "关于我们"]):
                continue

            items.append(line)

    # 去重（保持顺序）
    seen = set()
    unique_items = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)

    return unique_items[:15]  # 最多取15条


def extract_positioning(text: str, meta_desc: str, h1: str) -> str:
    """提取产品定位/一句话描述"""
    # 优先用 meta description
    if meta_desc and len(meta_desc) > 10:
        return meta_desc

    # 其次找页面前几段中的描述性文字
    lines = text.split("\n")
    for i, line in enumerate(lines[:20]):
        line = line.strip()
        # 定位描述通常 15-80 个字，包含"提供""助力""打造""面向"等关键词
        if 15 <= len(line) <= 80 and any(kw in line for kw in ["提供", "助力", "打造", "面向", "为", "帮助", "致力于", "新一代"]):
            return line

    return h1 or ""


# ---------------------------------------------------------------------------
# 主提取流程
# ---------------------------------------------------------------------------

def scrape_product(url: str, company: str = "", product_name: str = "") -> ProductInfo:
    """
    爬取单个产品页面，返回结构化的 ProductInfo
    """
    print(f"🔍 正在采集: {url}")

    info = ProductInfo(url=url, company=company, name=product_name)

    # 1. 获取页面
    html = fetch_page(url)
    if not html:
        info.extraction_notes.append("页面获取失败")
        return info

    time.sleep(REQUEST_DELAY)

    # 2. 基础提取
    raw_text = extract_text_from_html(html)
    info.raw_text = raw_text[:5000]  # 只存前5000字符，够用了

    title = extract_title(html)
    meta_desc = extract_meta_description(html)
    h1 = extract_h1(html)

    # 3. 产品名称
    if not info.name:
        info.name = h1 if h1 else title.split(" - ")[0].split("｜")[0].strip()

    # 4. 产品定位
    info.positioning = extract_positioning(raw_text, meta_desc, h1)

    # 5. 核心功能
    features = extract_section_items(raw_text, SECTION_KEYWORDS["core_features"])
    info.core_features = features

    # 6. 核心优势
    advantages = extract_section_items(raw_text, SECTION_KEYWORDS["core_advantages"])
    info.core_advantages = advantages

    # 7. 应用场景
    use_cases = extract_section_items(raw_text, SECTION_KEYWORDS["use_cases"])
    info.use_cases = use_cases

    # 8. 定价
    pricing_items = extract_section_items(raw_text, SECTION_KEYWORDS["pricing"])
    info.pricing = "\n".join(pricing_items) if pricing_items else ""

    # 9. 架构
    arch_items = extract_section_items(raw_text, SECTION_KEYWORDS["architecture"])
    info.architecture = "\n".join(arch_items) if arch_items else ""

    # 10. 客户案例
    customers = extract_section_items(raw_text, SECTION_KEYWORDS["customers"])
    info.customers = customers

    # 记录提取质量
    extracted_fields = sum([
        bool(info.positioning),
        bool(info.core_features),
        bool(info.core_advantages),
        bool(info.use_cases),
    ])
    info.extraction_notes.append(f"结构化提取字段: {extracted_fields}/4")

    print(f"  ✅ 完成: {info.name} (定位: {'是' if info.positioning else '否'}, 功能: {len(info.core_features)}条, 优势: {len(info.core_advantages)}条, 场景: {len(info.use_cases)}条)")

    return info


# ---------------------------------------------------------------------------
# 输出格式
# ---------------------------------------------------------------------------

def to_json(products: List[ProductInfo], output_path: str):
    """输出为 JSON 文件"""
    data = [asdict(p) for p in products]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n📄 JSON 已保存: {output_path}")


def to_markdown(products: List[ProductInfo], output_path: str, title: str = "竞品分析报告"):
    """输出为 Markdown 报告"""
    lines = [f"# {title}", ""]

    # 概览表
    lines.append("## 产品概览")
    lines.append("")
    lines.append("| 产品 | 所属公司 | 一句话定位 | 核心功能数 | 应用场景数 |")
    lines.append("|------|---------|-----------|-----------|-----------|")
    for p in products:
        pos_short = p.positioning[:50] + "..." if len(p.positioning) > 50 else p.positioning
        lines.append(f"| {p.name} | {p.company or '—'} | {pos_short or '—'} | {len(p.core_features)} | {len(p.use_cases)} |")
    lines.append("")

    # 每个产品的详情
    lines.append("## 产品详情")
    lines.append("")

    for i, p in enumerate(products, 1):
        lines.append(f"### {i}. {p.name}")
        lines.append("")
        lines.append(f"- **所属公司**：{p.company or '—'}")
        lines.append(f"- **产品链接**：[{p.url}]({p.url})")
        lines.append("")

        if p.positioning:
            lines.append("**产品定位**")
            lines.append("")
            lines.append(f"> {p.positioning}")
            lines.append("")

        if p.core_features:
            lines.append("**核心功能/能力**")
            lines.append("")
            for f in p.core_features:
                lines.append(f"- {f}")
            lines.append("")

        if p.core_advantages:
            lines.append("**核心优势**")
            lines.append("")
            for a in p.core_advantages:
                lines.append(f"- {a}")
            lines.append("")

        if p.use_cases:
            lines.append("**应用场景**")
            lines.append("")
            for uc in p.use_cases:
                lines.append(f"- {uc}")
            lines.append("")

        if p.pricing:
            lines.append("**定价模式**")
            lines.append("")
            lines.append(p.pricing)
            lines.append("")

        if p.architecture:
            lines.append("**产品架构**")
            lines.append("")
            lines.append(p.architecture)
            lines.append("")

        if p.customers:
            lines.append("**客户案例**")
            lines.append("")
            for c in p.customers:
                lines.append(f"- {c}")
            lines.append("")

        lines.append("---")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n📄 Markdown 报告已保存: {output_path}")


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="产品信息深度采集器 - 从官网URL提取结构化产品信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单URL模式，输出JSON
  python3 product_scraper.py --url "https://www.volcengine.com/product/DataAgent" --output dataagent.json

  # 多URL模式
  python3 product_scraper.py --urls "url1,url2,url3" --output products.json

  # 配置文件模式（输出Markdown报告）
  python3 product_scraper.py --config config.json --output report.md --format md

配置文件格式 (config.json):
  [
    {"company": "火山引擎", "product": "Data Agent", "url": "https://..."},
    {"company": "阿里云", "product": "智能小Q", "url": "https://..."}
  ]
        """
    )

    # 输入方式（三选一）
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--url", type=str, help="单个产品页面URL")
    input_group.add_argument("--urls", type=str, help="多个URL，用逗号分隔")
    input_group.add_argument("--config", type=str, help="配置文件路径（JSON格式）")

    # 输出参数
    parser.add_argument("--output", "-o", type=str, default="products_output.json",
                        help="输出文件路径 (默认: products_output.json)")
    parser.add_argument("--format", "-f", type=str, choices=["json", "md"], default="json",
                        help="输出格式: json 或 md (默认: json)")
    parser.add_argument("--title", type=str, default="竞品分析报告",
                        help="Markdown报告标题 (仅md格式有效)")

    args = parser.parse_args()

    try:
        products_config = []

        if args.url:
            products_config.append({"company": "", "product": "", "url": args.url.strip()})
        elif args.urls:
            urls = [u.strip() for u in args.urls.split(",") if u.strip()]
            for url in urls:
                products_config.append({"company": "", "product": "", "url": url})
        elif args.config:
            with open(args.config, "r", encoding="utf-8") as f:
                products_config = json.load(f)

        if not isinstance(products_config, list) or not products_config:
            raise TypeError("输入必须包含至少一个产品 URL")

        for index, config in enumerate(products_config, 1):
            if not isinstance(config, dict):
                raise TypeError(f"配置第 {index} 项必须是 JSON 对象")
            if "url" not in config:
                raise KeyError(f"配置第 {index} 项缺少 url")
            config["url"] = validate_public_url(config["url"])
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, KeyError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(f"🚀 开始采集，共 {len(products_config)} 个产品\n")

    # 逐个采集
    results = []
    for cfg in products_config:
        product = scrape_product(
            url=cfg["url"],
            company=cfg.get("company", ""),
            product_name=cfg.get("product", ""),
        )
        results.append(product)

    # 输出
    try:
        if args.format == "json":
            to_json(results, args.output)
        else:
            to_markdown(results, args.output, title=args.title)
    except (OSError, UnicodeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(f"\n🎉 全部完成！共采集 {len(results)} 个产品信息")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
