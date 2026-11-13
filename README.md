# 博主视频蒸馏 Skill

给一个博主主页，产出一套能直接交给 AI 复刻的内容包：

- 视频数据与 Top10 归因
- 每期选题明细与整体方向
- 文案风格
- 画面风格
- 3 条板块指令 + 1 条总蒸馏指令

最后用总指令，让 AI 出一期「口播稿 + 分镜表」。

## 安装

1. 复制整个文件夹到你的技能目录：

| 工具 | 技能目录 |
|---|---|
| Codex | ~/.codex/skills/blogger-video-distiller |
| DeepSeek Harness | ~/.agents/skills/blogger-video-distiller |
| Claude Code | ~/.claude/skills/blogger-video-distiller |

2. 需要 Python 3.9+（macOS 自带；Windows 装 python.org 版本，命令用 py 代替 python3）。不需要安装任何第三方包。

3. 配置归档位置：

```bash
cp config.example.json config.json
```

编辑 config.json，把 archive_root 改成你想放蒸馏结果的位置。不配置时默认在当前目录建「博主内容蒸馏」。

## 快速开始

在 Skill 目录下执行：

```bash
python3 scripts/manage_archive.py init --platform 抖音 --blogger-name "博主名" --profile-url "主页链接"
```

然后让 AI 按 SKILL.md 的流程填完 5 个板块，再执行：

```bash
python3 scripts/manage_archive.py render --blogger 博主名
python3 scripts/manage_archive.py check --blogger 博主名
```

check 全 OK 后，打开 蒸馏报告.html，把 复刻指令.md 和 总蒸馏指令.md 交给任意 AI 使用。

## 产物

```text
博主库/{平台}_{博主}/
  蒸馏报告.md      # 源文件
  蒸馏报告.html    # 阅读版，带复制按钮
  复刻指令.md      # 选题 / 文案 / 画面 三条
  总蒸馏指令.md    # 生成一期方案
  素材/            # 截图、字幕、导出数据
```

## 没有电脑控制能力怎么办

照样能用，走素材包模式：让用户上传主页截图、Top10 每期 3 帧画面、3—5 条逐字稿，然后按板块把指令贴进对话框。详见 references/portability.md。

## 常用命令

| 命令 | 作用 |
|---|---|
| init | 新建博主报告 |
| render | 生成 HTML，导出两个指令文件 |
| check | 交付前校验，不通过返回非零 |
| status | 看所有博主进度 |
| sample-plan --works N | 按作品数给出抽样建议 |
| reset-old --yes | 把旧格式档案移到备份目录 |
| reset-old --yes --purge | 直接删除旧格式档案 |

## 常见问题

**中文乱码**：确保文件是 UTF-8；Windows 终端可先执行 chcp 65001。

**HTML 打不开或样式错**：用浏览器直接打开 蒸馏报告.html，不要用编辑器预览。

**报告页脚日期不对**：改 frontmatter 的 抓取日期，重新 render。

**check 报「HTML 早于 Markdown」**：改完报告要重新 render。

**样本太少**：用 sample-plan 给出建议后补抽，低流量只留 2—5 条。

## 升级与卸载

升级时保留 archive_root 里的数据，只替换 Skill 目录。卸载直接删掉 Skill 文件夹，归档数据不受影响。
