#!/usr/bin/env python3
"""Render 蒸馏报告.md into a polished standalone HTML page and export prompt files."""

from __future__ import annotations

import html
import re
import sys
from datetime import date
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SHELL = SKILL_ROOT / "assets" / "report.html"
BT = chr(96)
FENCE = BT * 3
PROMPT_RE = re.compile(r"^" + FENCE + r"prompt\s*$")
FENCE_RE = re.compile(r"^" + FENCE + r"([A-Za-z0-9_-]*)\s*$")
CODE_RE = re.compile(BT + r"([^" + BT + r"]+)" + BT)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
META_SKIP = {"博主", "平台", "主页", "样本数", "抓取日期", "一句话"}


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, parts[2].lstrip("\n")


def md_inline(text: str) -> str:
    text = html.escape(text.strip())
    text = CODE_RE.sub(r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text,
    )
    return text


def slug(text: str, index: int) -> str:
    match = re.match(r"^(\d{1,3})", text.strip())
    return "s" + match.group(1) if match else "s" + str(index)


def bar_cell(raw: str) -> str | None:
    match = re.fullmatch(r"\[bar:(\d{1,3})\]", raw.strip())
    if not match:
        return None
    value = min(int(match.group(1)), 100)
    return (
        '<span class="bar"><i style="width:' + str(value) + '%"></i></span>'
        '<span class="num">' + str(value) + "</span>"
    )


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator(line: str) -> bool:
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells)


def render_table(lines: list[str]) -> str:
    header = split_row(lines[0])
    rows = [split_row(line) for line in lines[2:]]
    out = ['<div class="table-wrap"><table><thead><tr>']
    out.extend("<th>" + md_inline(cell) + "</th>" for cell in header)
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>")
        for index, cell in enumerate(row):
            bar = bar_cell(cell)
            cls = ' class="num"' if index > 0 and re.fullmatch(r"[\d.,%万亿]+", cell or "") else ""
            out.append("<td" + cls + ">" + (bar if bar else md_inline(cell)) + "</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def render_blocks(lines: list[str]) -> str:
    out: list[str] = []
    section_open = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        fence = FENCE_RE.match(stripped)
        if fence:
            lang = fence.group(1)
            body: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(FENCE):
                body.append(lines[i])
                i += 1
            i += 1
            code = html.escape("\n".join(body))
            if lang == "prompt":
                out.append(
                    '<div class="prompt"><div class="prompt-head">'
                    '<span class="tag"><i class="dot"></i>复刻指令</span>'
                    '<button class="copy" data-copy>复制</button></div>'
                    "<pre>" + code + "</pre></div>"
                )
            else:
                cls = ' class="lang-' + lang + '"' if lang else ""
                out.append("<pre><code" + cls + ">" + code + "</code></pre>")
            continue
        heading = HEADING_RE.match(stripped)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2)
            if level == 2:
                number = text[:2] if text[:2].isdigit() else ""
                label = text[3:] if number else text
                if section_open:
                    out.append("</section>")
                out.append(
                    '<section id="' + slug(text, len(out)) + '">'
                    '<h2><span class="idx">' + (number or "•") + "</span>"
                    + md_inline(label) + "</h2>"
                )
                section_open = True
            else:
                out.append("<h" + str(level) + ">" + md_inline(text) + "</h" + str(level) + ">")
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and is_separator(lines[i + 1]):
            block = [stripped]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            out.append(render_table(block))
            continue
        if stripped.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:])
                i += 1
            out.append("<ul>" + "".join("<li>" + md_inline(item) + "</li>" for item in items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s", stripped):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join("<li>" + md_inline(item) + "</li>" for item in items) + "</ol>")
            continue
        if stripped.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + " ".join(md_inline(q) for q in quote) + "</blockquote>")
            continue
        if stripped in {"---", "***"}:
            out.append("<hr>")
            i += 1
            continue
        para = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith(("#", "- ", ">", "|", FENCE)) or re.match(r"^\d+\.\s", nxt):
                break
            para.append(nxt)
            i += 1
        out.append("<p>" + md_inline(" ".join(para)) + "</p>")
    if section_open:
        out.append("</section>")
    return "\n".join(out)


def build_nav(lines: list[str]) -> str:
    items = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(FENCE):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(stripped)
        if match and len(match.group(1)) == 2:
            text = match.group(2)
            number = text[:2] if text[:2].isdigit() else ""
            label = text[3:] if number else text
            items.append((slug(text, len(items)), number, label))
    return "".join(
        '<a href="#' + anchor + '"><span class="n">' + number + "</span>" + html.escape(label) + "</a>"
        for anchor, number, label in items
    )


def build_cards(meta: dict[str, str]) -> str:
    cards = [
        (key, value)
        for key, value in meta.items()
        if key not in META_SKIP and value and value not in {"待填", "待补充"}
    ]
    if not cards:
        return ""
    return '<div class="kpis">' + "".join(
        '<div class="kpi"><div class="v">' + html.escape(value) + "</div>"
        '<div class="l">' + html.escape(key) + "</div></div>"
        for key, value in cards
    ) + "</div>"


def build_chips(meta: dict[str, str]) -> str:
    chips = []
    if meta.get("平台"):
        chips.append('<span class="chip accent">' + html.escape(meta["平台"]) + "</span>")
    if meta.get("样本数"):
        chips.append('<span class="chip">样本 <b>' + html.escape(meta["样本数"]) + "</b> 条</span>")
    if meta.get("抓取日期"):
        chips.append('<span class="chip">抓取 <b>' + html.escape(meta["抓取日期"]) + "</b></span>")
    if meta.get("主页"):
        url = html.escape(meta["主页"], quote=True)
        chips.append('<a class="chip" href="' + url + '" target="_blank" rel="noopener">查看主页</a>')
    return "".join(chips)


def extract_prompts(lines: list[str]) -> list[dict[str, str]]:
    prompts: list[dict[str, str]] = []
    section = ""
    heading = ""
    i = 0
    in_fence = False
    while i < len(lines):
        stripped = lines[i].strip()
        if in_fence:
            if stripped.startswith(FENCE):
                in_fence = False
            i += 1
            continue
        match = HEADING_RE.match(stripped)
        if match and len(match.group(1)) == 2:
            section = match.group(2)
        elif match and len(match.group(1)) == 3:
            heading = match.group(2)
        if stripped.startswith(FENCE):
            if PROMPT_RE.match(stripped):
                body: list[str] = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith(FENCE):
                    body.append(lines[i])
                    i += 1
                title = re.sub(r"^[\d.]+\s*", "", heading or section)
                prompts.append(
                    {"section": section, "title": title, "content": "\n".join(body).strip()}
                )
            else:
                in_fence = True
        i += 1
    return prompts


def render(blogger_dir: Path, quiet: bool = False) -> dict[str, Path]:
    md_path = blogger_dir / "蒸馏报告.md"
    if not md_path.exists():
        raise FileNotFoundError("缺少蒸馏报告：" + str(md_path))
    text = md_path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    lines = body.splitlines()
    name = meta.get("博主") or blogger_dir.name.split("_", 1)[-1]
    title = name + "｜内容蒸馏报告"
    subtitle = meta.get("一句话") or "这一个博主为什么能起来，以及怎么复刻。"

    page = SHELL.read_text(encoding="utf-8")
    page = (
        page.replace("{{TITLE}}", html.escape(title))
        .replace("{{SUBTITLE}}", html.escape(subtitle))
        .replace("{{CHIPS}}", build_chips(meta))
        .replace("{{NAV}}", build_nav(lines))
        .replace("{{CARDS}}", build_cards(meta))
        .replace("{{BODY}}", render_blocks(lines))
        .replace("{{FOOTER_LEFT}}", "数据截至 " + html.escape(meta.get("抓取日期", "未标注")))
        .replace("{{FOOTER_RIGHT}}", "由 blogger-video-distiller 生成 · " + date.today().isoformat())
    )
    html_path = blogger_dir / "蒸馏报告.html"
    html_path.write_text(page, encoding="utf-8")

    prompts = extract_prompts(lines)
    section_prompts = [p for p in prompts if not p["section"].startswith("05")]
    master = [p for p in prompts if p["section"].startswith("05")]
    cmd_path = blogger_dir / "复刻指令.md"
    if section_prompts:
        parts = [
            "# " + name + "｜复刻指令",
            "",
            "> 用法：一条指令配一次素材。先替换【】里的变量，再把指令整体发给 AI。",
            "> 适用：ChatGPT、Claude、Gemini、DeepSeek、豆包、Kimi、通义等，纯文本即可。",
            "",
        ]
        for item in section_prompts:
            parts += ["## " + item["title"], "", FENCE + "text", item["content"], FENCE, ""]
        cmd_path.write_text("\n".join(parts), encoding="utf-8")
    master_path = blogger_dir / "总蒸馏指令.md"
    if master:
        master_path.write_text(
            "\n".join(
                [
                    "# " + name + "｜总蒸馏指令",
                    "",
                    "> 用法：把下面的指令整段发给 AI，填好【本次输入】，即可产出口播稿与分镜表。",
                    "> 如果模型一次输出不完，先让它出「选题 + 标题」，确认后再出「口播稿」，最后出「分镜表」。",
                    "",
                    FENCE + "text",
                    master[0]["content"],
                    FENCE,
                    "",
                ]
            ),
            encoding="utf-8",
        )
    if not quiet:
        print("HTML：" + str(html_path))
        if section_prompts:
            print("复刻指令：" + str(cmd_path) + "（" + str(len(section_prompts)) + " 条）")
        if master:
            print("总蒸馏指令：" + str(master_path))
    return {"html": html_path, "prompts": cmd_path, "master": master_path}


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    render(target)


if __name__ == "__main__":
    main()
