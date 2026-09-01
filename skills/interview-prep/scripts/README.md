# 脚本使用说明

本目录包含两个辅助脚本，用于面试准备 Skill 的数据采集和提取。

---

## 脚本清单

| 脚本 | 用途 | 依赖 | 适用场景 |
|------|------|------|---------|
| `product_scraper.py` | 静态页面爬虫 | requests, beautifulsoup4 | 批量抓取静态HTML页面 |
| `product_extractor.py` | 文本结构化提取器 | 无（纯Python标准库+正则） | 从纯文本中提取产品功能/优势/场景 |

---

## product_scraper.py（静态页面爬虫）

### 功能
从指定的产品官网URL中，抓取HTML并提取产品信息（定位、功能、优势、场景等）。

### 限制
- 只能抓取**静态页面**，JS渲染的SPA页面抓不到内容
- 营销型产品页（图片多、文字少）提取效果差
- 只允许解析到公网地址的 HTTP/HTTPS 页面；本机、内网、链路本地和保留地址会被拒绝
- 最多跟随 5 次跳转，只接收 HTML，单个响应上限为 5 MiB
- 不适合登录页面、内部系统、私有文档或包含个人信息的 URL

### 使用方式

```bash
# 单个URL，输出JSON
python3 product_scraper.py \
  --url "https://example.com/product" \
  --output product.json

# 多个URL（逗号分隔）
python3 product_scraper.py \
  --urls "url1,url2,url3" \
  --output products.json

# 配置文件模式（输出Markdown报告）
python3 product_scraper.py \
  --config config.json \
  --output report.md \
  --format md
```

### 配置文件格式

```json
[
  {
    "company": "火山引擎",
    "product": "Data Agent",
    "url": "https://www.volcengine.com/product/DataAgent"
  }
]
```

---

## product_extractor.py（结构化提取器）

### 功能
从产品页面的纯文本中，基于关键词规则和句式特征，提取结构化的产品信息。

### 设计定位
- 这是一个**辅助工具**，不是主力提取器
- 正式研究优先使用能保留来源的浏览工具和语义提取 Prompt
- 规则提取器用于：快速预览、兜底、批量预处理
- 无论使用规则或大模型，结果都需要回到原始页面核对

### 使用方式

```bash
# 从文本文件提取
python3 product_extractor.py \
  --input page.txt \
  --name "产品名" \
  --company "公司名" \
  --output product.json

# 从标准输入管道读取
cat page.txt | python3 product_extractor.py \
  --stdin \
  --output product.json

# 批量处理 + Markdown报告输出
python3 product_extractor.py \
  --batch batch_data.json \
  --output report.md \
  --format md \
  --title "竞品分析报告"
```

### 批量数据格式

```json
[
  {
    "name": "产品名称",
    "company": "公司名",
    "url": "https://...",
    "text": "页面纯文本内容..."
  }
]
```

---

## 什么时候用脚本，什么时候用大模型？

| 场景 | 推荐方案 | 原因 |
|------|---------|------|
| 快速浏览、初步筛选 | 规则提取器 | 速度快、零成本 |
| 正式面试准备、需要可追溯结果 | 浏览工具 + 语义提取 Prompt | 能结合上下文并保留来源 |
| 结构非常规整的页面（如文档页） | 规则提取器 | 规则就能搞定，省Token |
| 营销型产品页、内容分散 | 大模型提取 | 需要语义理解和归纳 |
| 批量处理10+个页面 | 规则提取（先过滤）+ 大模型（精选后深扒） | 兼顾效率和质量 |

---

## 安装依赖

推荐使用虚拟环境，避免修改系统 Python：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install requests beautifulsoup4
```

也可以用 `uv` 临时提供依赖：

```bash
uv run --with requests --with beautifulsoup4 \
  python product_scraper.py \
  --url "https://example.com/product" \
  --output product.json
```

当前脚本没有实现 Playwright 或浏览器自动化，不需要安装相关依赖。

## 网络与使用边界

- 只抓取用户明确用于研究的公开产品页面，运行前确认网站条款和 robots 规则。
- 不关闭 TLS 验证，不绕过登录、验证码、付费墙或访问控制。
- 页面获取失败时改用浏览工具或请用户提供公开页面文本，不尝试访问内部地址。
- 输出仍需人工核对来源和查询日期；规则提取结果不能直接当作已验证产品事实。
