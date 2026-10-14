#!/usr/bin/env python3
"""素材提取：从简历/项目文档中提取纯文本，供润色前盘点使用。

用法:
    python3 extract_material.py <file>                # 自动识别扩展名
    python3 extract_material.py <file> --out out.txt
    python3 extract_material.py resume.docx --full    # 连页眉/页脚/脚注一起提取

支持:
    .docx / .docm / .dotx —— 解析 word/document.xml，支持 sdt 内容控件与嵌套表格，
                             表格按行输出（简历常整表存放，比编辑器预览完整）
    .html / .htm          —— 剥离 script/style/base64 后提取正文，表格保留 ` || ` 结构
    .pdf                  —— 优先 pypdf，缺失时自动回退 pdftotext；正文过少提示扫描件

说明:
    - docx 一律优先用本脚本，不要依赖编辑器 MCP 的文本预览（会截断长文本）。
    - 输出中 ` || ` 分隔表格单元格，`--- 表格N ---` 标记表格边界。
    - 扫描件/图片型 PDF 或图片简历：本脚本提不出内容，改用视觉读取（Read 工具读图）。
"""
import sys
import os
import re
import zipfile
import shutil
import subprocess
import argparse
import html as _html
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def _el_text(el):
    """收集元素下所有 w:t 文本。"""
    return ''.join(t.text or '' for t in el.iter(W + 't'))


def _cell_text(tc, counter):
    """表格单元格：段落 + 嵌套表格递归展开。"""
    parts = []
    for child in tc:
        if child.tag == W + 'p':
            txt = _el_text(child).strip()
            if txt:
                parts.append(txt)
        elif child.tag == W + 'tbl':
            parts.append(_render_table(child, counter))
    return '\n'.join(parts)


def _render_table(tbl, counter):
    counter[0] += 1
    lines = [f'--- 表格{counter[0]} ---']
    for tr in tbl.findall(W + 'tr'):
        cells = [_cell_text(tc, counter) for tc in tr.findall(W + 'tc')]
        lines.append(' || '.join(cells))
    return '\n'.join(lines)


def _walk_blocks(container, lines, counter):
    """递归遍历段落/表格容器，穿透 w:sdt（内容控件，Word 模板简历常见）。"""
    for child in container:
        tag = child.tag
        if tag == W + 'p':
            txt = _el_text(child).strip()
            if txt:
                lines.append(txt)
        elif tag == W + 'tbl':
            lines.append(_render_table(child, counter))
        elif tag == W + 'sdt':
            content = child.find(W + 'sdtContent')
            if content is not None:
                _walk_blocks(content, lines, counter)
        elif tag == W + 'sectPr':
            continue
        else:
            # 其他含子块结构的元素兜底下探
            if child.find(W + 'p') is not None or child.find(W + 'tbl') is not None:
                _walk_blocks(child, lines, counter)


def _docx_part_text(z, name):
    if name not in z.namelist():
        return ''
    root = ET.fromstring(z.read(name).decode('utf-8', errors='ignore'))
    lines = []
    _walk_blocks(root, lines, [0])
    return '\n'.join(lines)


def extract_docx(path, full=False):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if 'word/document.xml' not in names:
            raise SystemExit('[error] 未找到 word/document.xml，可能不是标准 docx')
        root = ET.fromstring(z.read('word/document.xml').decode('utf-8', errors='ignore'))
        body = root.find(W + 'body')
        if body is None:
            raise SystemExit('[error] 未找到 body')
        lines, counter = [], [0]
        _walk_blocks(body, lines, counter)
        text = '\n'.join(lines)
        if full:
            extras = []
            part_re = re.compile(r'word/(header|footer|footnotes|endnotes)\d*\.xml$')
            for name in sorted(names):
                if part_re.match(name):
                    t = _docx_part_text(z, name)
                    if t:
                        extras.append(f'--- {name} ---\n{t}')
            if extras:
                text += '\n\n' + '\n\n'.join(extras)
    return text


def _strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', _html.unescape(s)).strip()


def extract_html(path):
    s = open(path, encoding='utf-8', errors='ignore').read()
    s = re.sub(r'<script[\s\S]*?</script>', '', s, flags=re.I)
    s = re.sub(r'<style[\s\S]*?</style>', '', s, flags=re.I)
    s = re.sub(r'data:image/[^"\')>\s]+', '', s)

    # 表格先行提取，保留 ` || ` 结构（与 docx 路径行为一致）
    table_blocks, tbl_no = [], [0]

    def _grab_table(m):
        tbl_no[0] += 1
        rows = [f'--- 表格{tbl_no[0]} ---']
        for tr in re.findall(r'<tr[\s\S]*?</tr>', m.group(0), flags=re.I):
            cells = [_strip_tags(td) for td in
                     re.findall(r'<t[dh][\s\S]*?</t[dh]>', tr, flags=re.I)]
            if cells:
                rows.append(' || '.join(cells))
        table_blocks.append('\n'.join(rows))
        return f'\n[[TABLE_{tbl_no[0]}]]\n'

    s = re.sub(r'<table[\s\S]*?</table>', _grab_table, s, flags=re.I)
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.I)
    s = re.sub(r'</(p|div|li|tr|h[1-6])>', '\n', s, flags=re.I)
    s = re.sub(r'<[^>]+>', '', s)
    s = _html.unescape(s)
    for i, block in enumerate(table_blocks, 1):
        s = s.replace(f'[[TABLE_{i}]]', block)
    lines = [ln.strip() for ln in s.split('\n')]
    lines = [ln for ln in lines if ln and len(ln) > 1]
    return '\n'.join(lines)


def _pdf_with_pypdf(path):
    from pypdf import PdfReader
    reader = PdfReader(path)
    out = []
    for i, page in enumerate(reader.pages, 1):
        txt = (page.extract_text() or '').strip()
        if txt:
            out.append(f'--- 第{i}页 ---')
            out.append(txt)
    return '\n'.join(out)


def _pdf_with_pdftotext(path):
    exe = shutil.which('pdftotext')
    if not exe:
        return None
    proc = subprocess.run([exe, '-layout', path, '-'],
                          capture_output=True, text=True, errors='ignore')
    if proc.returncode != 0:
        return None
    out = []
    for i, chunk in enumerate(proc.stdout.split('\f'), 1):
        txt = chunk.strip()
        if txt:
            out.append(f'--- 第{i}页 ---')
            out.append(txt)
    return '\n'.join(out)


def extract_pdf(path):
    text, engine = None, None
    try:
        text, engine = _pdf_with_pypdf(path), 'pypdf'
    except ImportError:
        text = _pdf_with_pdftotext(path)
        engine = 'pdftotext' if text is not None else None
    if text is None:
        raise SystemExit(
            '[error] 需要 pypdf（pip install pypdf）或系统 pdftotext（brew install poppler）')
    if len(text) < 60:
        print('[warn] 提取正文极少，疑似扫描件/图片型 PDF——请改用视觉读取（Read 工具直接读该 PDF）',
              file=sys.stderr)
    return text


EXTRACTORS = {
    '.docx': extract_docx, '.docm': extract_docx, '.dotx': extract_docx,
    '.html': extract_html, '.htm': extract_html,
    '.pdf': extract_pdf,
}


def main():
    ap = argparse.ArgumentParser(description='从简历/项目文档提取纯文本')
    ap.add_argument('file', help='输入文件路径')
    ap.add_argument('--out', help='输出文件路径（默认打印到 stdout）')
    ap.add_argument('--full', action='store_true',
                    help='docx 附加页眉/页脚/脚注内容')
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        raise SystemExit(f'[error] 文件不存在: {args.file}')
    ext = os.path.splitext(args.file)[1].lower()
    fn = EXTRACTORS.get(ext)
    if not fn:
        raise SystemExit(f'[error] 不支持的格式 {ext}，支持: {", ".join(EXTRACTORS)}')

    text = fn(args.file, full=True) if (fn is extract_docx and args.full) else fn(args.file)
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'[ok] 已写入 {args.out}（{len(text)} 字符）')
    else:
        print(text)


if __name__ == '__main__':
    main()
