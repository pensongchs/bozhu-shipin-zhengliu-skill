#!/usr/bin/env python3
"""Manage single-blogger distillation folders: init, render, check, status, sample-plan."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / "assets"
CONFIG = SKILL_ROOT / "config.json"
TEMPLATE = ASSETS / "蒸馏报告模板.md"
REQUIRED_SECTIONS = ["01", "02", "03", "04", "05"]
PENDING_MARKS = ["待蒸馏", "待补充", "{{"]
BT = chr(96)
FENCE = BT * 3

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_report import render  # noqa: E402


def resolve_root(cli_root: str | None) -> Path:
    if cli_root:
        return Path(cli_root).expanduser().resolve()
    env = os.environ.get("BLOGGER_DISTILL_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    if CONFIG.exists():
        try:
            data = json.loads(CONFIG.read_text(encoding="utf-8"))
            value = data.get("archive_root")
            if value:
                return Path(value).expanduser().resolve()
        except (json.JSONDecodeError, OSError):
            pass
    return (Path.cwd() / "博主内容蒸馏").resolve()


def safe_name(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|]+', "-", value.strip())
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" .-")
    if not value:
        raise ValueError("名称不能为空")
    return value[:80]


def blogger_dir(root: Path, platform: str, name: str) -> Path:
    return root / "博主库" / (safe_name(platform) + "_" + safe_name(name))


def init(root: Path, platform: str, name: str, profile: str) -> Path:
    folder = blogger_dir(root, platform, name)
    (folder / "素材").mkdir(parents=True, exist_ok=True)
    report = folder / "蒸馏报告.md"
    if report.exists():
        print("已存在，未覆盖：" + str(report))
        return folder
    text = TEMPLATE.read_text(encoding="utf-8")
    text = (
        text.replace("{{BLOGGER_NAME}}", name)
        .replace("{{PLATFORM}}", platform)
        .replace("{{PROFILE_URL}}", profile or "待补充")
        .replace("{{CAPTURE_DATE}}", date.today().isoformat())
    )
    report.write_text(text, encoding="utf-8")
    print("博主目录：" + str(folder))
    print("报告模板：" + str(report))
    print("下一步：填完 01—05，然后运行 render 与 check")
    return folder


def read_meta(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta


def count_table_rows(text: str, section: str) -> int:
    rows = 0
    inside = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## " + section):
            inside = True
            continue
        if inside and stripped.startswith("## "):
            break
        if inside and stripped.startswith("|") and not re.fullmatch(r"\|[\s:|-]+\|", stripped):
            rows += 1
    return max(rows - 2, 0)


def check_one(folder: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    report = folder / "蒸馏报告.md"
    if not report.exists():
        return ["缺少 蒸馏报告.md"], warnings
    text = report.read_text(encoding="utf-8")
    meta = read_meta(report)
    for key in ("博主", "平台", "样本数", "抓取日期", "一句话"):
        if not meta.get(key) or meta[key] in {"待填", "待补充"}:
            errors.append("frontmatter 缺少或未填：" + key)
    required = {"博主", "平台", "样本数", "抓取日期", "一句话"}
    for key, value in meta.items():
        if value == "待填" and key not in required:
            errors.append("frontmatter 仍有待填项：" + key)
    if "【博主名】" in text:
        errors.append("指令里仍有未替换的【博主名】")
    for section in REQUIRED_SECTIONS:
        if not re.search(r"(?m)^## " + section + r"\s", text):
            errors.append("缺少板块 " + section)
    for mark in PENDING_MARKS:
        if mark in text:
            errors.append("仍有未填写标记：" + mark)
    prompts = len(re.findall(r"(?m)^" + FENCE + "prompt", text))
    if prompts < 4:
        errors.append("复刻指令不足：" + str(prompts) + " 条（需要 3 条板块指令 + 1 条总指令）")
    master = text.split("## 05", 1)[-1]
    if FENCE + "prompt" not in master:
        errors.append("05 板块缺少总蒸馏指令")
    try:
        sample = int(meta.get("样本数", "0"))
        if sample < 1:
            errors.append("样本数为 0，尚未蒸馏")
        elif sample < 5:
            warnings.append("样本数偏少（" + str(sample) + " 条），结论只能标为初步观察")
        rows = count_table_rows(text, "01")
        if sample and rows and rows < min(sample, 5):
            warnings.append("全量样本表行数（" + str(rows) + "）少于样本数（" + str(sample) + "）")
    except ValueError:
        errors.append("样本数不是整数：" + meta.get("样本数", ""))
    html = folder / "蒸馏报告.html"
    if not html.exists():
        errors.append("尚未渲染 HTML，运行 render")
    elif html.stat().st_mtime < report.stat().st_mtime:
        warnings.append("HTML 早于 Markdown，需要重新 render")
    return errors, warnings


def iter_bloggers(root: Path, only: str | None = None) -> list[Path]:
    base = root / "博主库"
    if not base.is_dir():
        return []
    folders = sorted(p for p in base.iterdir() if p.is_dir())
    if only:
        folders = [p for p in folders if only in p.name]
    return folders


def do_render(root: Path, only: str | None) -> int:
    folders = iter_bloggers(root, only)
    if not folders:
        print("没有找到博主目录：" + str(root / "博主库"))
        return 1
    failed = 0
    for folder in folders:
        try:
            render(folder)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print("失败 " + folder.name + "：" + str(exc))
    return 1 if failed else 0


def do_check(root: Path, only: str | None) -> int:
    folders = iter_bloggers(root, only)
    if not folders:
        print("没有找到博主目录")
        return 1
    total_errors = 0
    for folder in folders:
        errors, warnings = check_one(folder)
        if errors:
            total_errors += 1
            print("FAIL " + folder.name)
            for item in errors:
                print("  - " + item)
        else:
            print("OK   " + folder.name)
        for item in warnings:
            print("  ! " + item)
    print("\n结果：" + str(total_errors) + " 个博主需要补齐")
    return 1 if total_errors else 0


def do_status(root: Path) -> int:
    folders = iter_bloggers(root)
    if not folders:
        print("归档根目录：" + str(root) + "（暂无博主）")
        return 0
    print("归档根目录：" + str(root))
    for folder in folders:
        report = folder / "蒸馏报告.md"
        if not report.exists():
            print("- " + folder.name + "：缺少报告")
            continue
        meta = read_meta(report)
        text = report.read_text(encoding="utf-8")
        sections = sum(1 for s in REQUIRED_SECTIONS if re.search(r"(?m)^## " + s + r"\s", text))
        prompts = len(re.findall(r"(?m)^" + FENCE + "prompt", text))
        html = "有" if (folder / "蒸馏报告.html").exists() else "无"
        print(
            "- " + folder.name
            + "：样本 " + meta.get("样本数", "?")
            + "｜板块 " + str(sections) + "/5"
            + "｜指令 " + str(prompts)
            + "｜HTML " + html
        )
    return 0


def sample_plan(works: int) -> str:
    if works <= 30:
        plan = "全量 " + str(works) + " 条：高流量 5—10 + 低流量 2—3"
    elif works <= 100:
        plan = "20—25 条：Top10 + 中位 8—10 + 低流量 3—5"
    elif works <= 300:
        plan = "25—30 条：Top10 + 中位 10 + 低流量 5"
    else:
        plan = "30—35 条：Top10 + 中位 12 + 低流量 5—8"
    return (
        "作品数 " + str(works) + " → 建议样本：" + plan + "\n"
        "热度基线：账号中位数。Top 取 ≥2 倍中位，低流量取 ≤0.5 倍中位。\n"
        "低流量样本只用于对照，不做趋势结论；数据缺失的期数在表里标「未获取」。"
    )


def do_reset(root: Path, purge: bool, yes: bool) -> int:
    targets: list[Path] = []
    for name in ("跨博主汇总", "工作台.md"):
        path = root / name
        if path.exists():
            targets.append(path)
    for folder in iter_bloggers(root):
        if not (folder / "蒸馏报告.md").exists():
            targets.append(folder)
            continue
        for name in ("单条拆解", "综合蒸馏", "原创选题", "视频索引.md", "博主档案.md"):
            path = folder / name
            if path.exists():
                targets.append(path)
    if not targets:
        print("没有发现旧格式文件")
        return 0
    if not yes:
        print("将处理以下旧格式内容（加 --yes 执行）：")
        for path in targets:
            print("  - " + str(path.relative_to(root)))
        return 0
    if purge:
        for path in targets:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        print("已删除 " + str(len(targets)) + " 项旧格式内容")
        return 0
    backup = root / ("_旧格式归档_" + date.today().strftime("%Y%m%d"))
    backup.mkdir(parents=True, exist_ok=True)
    for path in targets:
        rel = path.relative_to(root)
        dest = backup / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))
    print("已移动到：" + str(backup) + "（共 " + str(len(targets)) + " 项）")
    print("确认无误后可删除该目录，或用 --purge --yes 直接删除。")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="博主视频蒸馏：单博主报告工作流")
    parser.add_argument("--root", default=None, help="归档根目录，默认读 config.json 或环境变量")
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="新建一个博主的报告")
    init_parser.add_argument("--platform", required=True)
    init_parser.add_argument("--blogger-name", required=True)
    init_parser.add_argument("--profile-url", default="")

    render_parser = sub.add_parser("render", help="Markdown 渲染 HTML，并导出指令文件")
    render_parser.add_argument("--blogger", default=None)

    check_parser = sub.add_parser("check", help="交付前校验")
    check_parser.add_argument("--blogger", default=None)

    sub.add_parser("status", help="查看所有博主进度")

    plan_parser = sub.add_parser("sample-plan", help="按作品数给出抽样建议")
    plan_parser.add_argument("--works", type=int, required=True)

    reset_parser = sub.add_parser("reset-old", help="清理旧格式档案（默认只列出）")
    reset_parser.add_argument("--purge", action="store_true", help="直接删除而不是移动到备份目录")
    reset_parser.add_argument("--yes", action="store_true", help="确认执行")

    args = parser.parse_args()
    root = resolve_root(args.root)

    if args.command == "init":
        init(root, args.platform, args.blogger_name, args.profile_url)
    elif args.command == "render":
        raise SystemExit(do_render(root, args.blogger))
    elif args.command == "check":
        raise SystemExit(do_check(root, args.blogger))
    elif args.command == "status":
        raise SystemExit(do_status(root))
    elif args.command == "sample-plan":
        print(sample_plan(args.works))
    else:
        raise SystemExit(do_reset(root, args.purge, args.yes))


if __name__ == "__main__":
    main()
