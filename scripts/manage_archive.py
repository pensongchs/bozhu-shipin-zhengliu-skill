#!/usr/bin/env python3
"""Initialize and maintain the blogger video distillation archive."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / "assets"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_ROOT = PROJECT_ROOT / "outputs" / "博主内容蒸馏"


def safe_name(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|]+', "-", value.strip())
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" .-")
    if not value:
        raise ValueError("名称不能为空")
    return value[:80]


def render(template_name: str, replacements: dict[str, str]) -> str:
    text = (ASSETS / template_name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def init_root(root: Path) -> list[Path]:
    created: list[Path] = []
    for folder in (root / "待处理", root / "博主库", root / "跨博主汇总"):
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            created.append(folder)
    today = date.today().isoformat()
    files = {
        root / "工作台.md": render("工作台模板.md", {"CAPTURE_DATE": today}),
        root / "跨博主汇总" / "跨博主内容规律.md": render(
            "跨博主内容规律模板.md", {"CAPTURE_DATE": today}
        ),
        root / "跨博主汇总" / "跨博主原创选题池.md": render(
            "跨博主原创选题池模板.md", {"CAPTURE_DATE": today}
        ),
    }
    for path, content in files.items():
        if write_if_missing(path, content):
            created.append(path)
    return created


def blogger_path(root: Path, platform: str, blogger_name: str) -> Path:
    return root / "博主库" / f"{safe_name(platform)}_{safe_name(blogger_name)}"


def init_blogger(
    root: Path, platform: str, blogger_name: str, profile_url: str
) -> tuple[Path, list[Path]]:
    init_root(root)
    folder = blogger_path(root, platform, blogger_name)
    for child in ("单条拆解", "综合蒸馏", "原创选题"):
        (folder / child).mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    values = {
        "PLATFORM": platform,
        "BLOGGER_NAME": blogger_name,
        "PROFILE_URL": profile_url or "待补充",
        "CAPTURE_DATE": today,
    }
    files = {
        folder / "博主档案.md": (
            f"# {blogger_name}｜博主档案\n\n"
            f"- 平台：{platform}\n"
            f"- 主页：{profile_url or '待补充'}\n"
            f"- 建档日期：{today}\n"
            "- 账号定位：待蒸馏\n"
            "- 目标受众：待蒸馏\n"
            "- 当前样本数：0\n"
        ),
        folder / "视频索引.md": (
            f"# {blogger_name}｜视频索引\n\n"
            "| 发布时间 | 视频标题 | 链接 | 抓取日期 | 材料完整度 | 拆解文件 |\n"
            "|---|---|---|---|---|---|\n"
        ),
        folder / "综合蒸馏" / "博主内容基因.md": render(
            "博主内容基因模板.md", values
        ),
        folder / "原创选题" / "原创选题池.md": render("原创选题池模板.md", values),
    }
    created: list[Path] = []
    for path, content in files.items():
        if write_if_missing(path, content):
            created.append(path)
    return folder, created


def add_video(
    root: Path,
    platform: str,
    blogger_name: str,
    title: str,
    url: str,
    published_date: str,
) -> tuple[Path, bool]:
    folder, _ = init_blogger(root, platform, blogger_name, "")
    today = date.today().isoformat()
    published = published_date or "日期不详"
    filename_date = published_date or today
    path = folder / "单条拆解" / f"{safe_name(filename_date)}_{safe_name(title)}.md"
    content = render(
        "单条视频拆解模板.md",
        {
            "PLATFORM": platform,
            "BLOGGER_NAME": blogger_name,
            "VIDEO_TITLE": title,
            "VIDEO_URL": url or "待补充",
            "PUBLISHED_DATE": published,
            "CAPTURE_DATE": today,
        },
    )
    return path, write_if_missing(path, content)


def main() -> None:
    parser = argparse.ArgumentParser(description="管理博主视频蒸馏归档")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-root", help="初始化蒸馏工作台")

    blogger_parser = subparsers.add_parser("init-blogger", help="新增博主档案")
    blogger_parser.add_argument("--platform", required=True)
    blogger_parser.add_argument("--blogger-name", required=True)
    blogger_parser.add_argument("--profile-url", default="")

    video_parser = subparsers.add_parser("add-video", help="新增单条视频拆解文件")
    video_parser.add_argument("--platform", required=True)
    video_parser.add_argument("--blogger-name", required=True)
    video_parser.add_argument("--title", required=True)
    video_parser.add_argument("--url", default="")
    video_parser.add_argument("--published-date", default="")

    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "init-root":
        created = init_root(root)
        print(f"工作台：{root}")
        print(f"新增：{len(created)} 项")
    elif args.command == "init-blogger":
        folder, created = init_blogger(
            root, args.platform, args.blogger_name, args.profile_url
        )
        print(f"博主目录：{folder}")
        print(f"新增：{len(created)} 个文件")
    else:
        path, created = add_video(
            root,
            args.platform,
            args.blogger_name,
            args.title,
            args.url,
            args.published_date,
        )
        print(f"视频拆解：{path}")
        print("状态：已创建" if created else "状态：已存在，未覆盖")


if __name__ == "__main__":
    main()
