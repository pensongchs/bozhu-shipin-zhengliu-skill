# 博主视频蒸馏 Skill

给一个博主主页，产出一套能直接交给 AI 复刻的内容包：

- 视频数据与 Top10 归因
- 每期选题明细与整体方向
- 文案风格
- 画面风格
- 3 条板块指令 + 1 条总蒸馏指令

最后用总指令，让 AI 出一期「口播稿 + 分镜表」。

## 安装

把解压后的 `blogger-video-distiller` 文件夹放到 AI 工具的技能目录，确保文件夹里直接是 `SKILL.md`。

| 工具 | 技能位置 |
|---|---|
| Codex | 用户目录下的 `.agents/skills/blogger-video-distiller`。Windows 也可放在当前工作项目的 `.agents/skills/blogger-video-distiller` |
| DeepSeek Harness | 用户目录下的 `.agents/skills/blogger-video-distiller` |
| Claude Code | 用户目录下的 `.claude/skills/blogger-video-distiller` |

使用浏览器采集前，确认当前 AI 会话已启用能操作播放器、看到正片画面，并且用户也能接管的浏览器或电脑控制。渲染和校验报告需要 Python 3.9+，仅用标准库。Windows 可在 PowerShell 运行 `py -3 --version` 检查；如果使用的是已配置的 `python`，把以下 `py -3` 换成 `python`。macOS 或 Linux 使用 `python3`。

需要指定归档位置时，将 `config.example.json` 另存为 `config.json`，修改其中的 `archive_root`。Windows 的 JSON 路径可写成 `D:/博主内容蒸馏`。默认归档在当前工作目录的「博主内容蒸馏」。

## 快速开始

在 AI 里调用：

> 用 $blogger-video-distiller 蒸馏这个抖音账号：【主页链接或抖音号】。用浏览器打开一条公开视频试播。如果需要登录，请把浏览器交给我用非主账号扫码。能看到正片后开始抽样。

登录时只在抖音网页和手机 App 操作。完成后把控制交回 AI。出现访问频繁或账号异常提示时暂停浏览。详细步骤及画面、口播的核对标准见 [跨工具与抖音访问流程](references/portability.md)。

AI 可在 Skill 目录调用脚本建档、渲染和校验。Windows PowerShell 命令：

```powershell
py -3 scripts/manage_archive.py init --platform 抖音 --blogger-name "博主名" --profile-url "主页链接"
py -3 scripts/manage_archive.py render --blogger "博主名"
py -3 scripts/manage_archive.py check --blogger "博主名"
```

等 5 个板块填完再执行 `render` 和 `check`。校验通过后打开「蒸馏报告.html」，把「复刻指令.md」和「总蒸馏指令.md」交给 AI 使用。

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

可上传主页或数据截图、对应作品的正片截图或视频，以及字幕或逐字稿。AI 按拿到的素材继续分析，注明缺失项。见 [素材包模式](references/portability.md#素材包模式)。

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
