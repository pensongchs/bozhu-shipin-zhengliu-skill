# 维护约定

这个 Skill 由 Codex 和 DeepSeek Harness 两个 Agent 共同维护，也会分发给学员。改动必须可追溯、可回滚。

## 唯一真源

- Git 仓库：pensongchs/bozhu-shipin-zhengliu-skill
- 唯一副本：~/Documents/Codex skill/博主视频蒸馏
- 软链：~/Documents/自媒体专用/.agents/skills/blogger-video-distiller 与 ~/.agents/skills/blogger-video-distiller 都指向这里

只存在这一份文件，软链不复制内容。改这里就是改全部，**不要另建副本或把软链改回目录**。

## 版本

- SKILL.md frontmatter 的 version 必须与 CHANGELOG 最新条目一致。
- 破坏性改动（产物结构、文件命名、模板字段）升主版本，并在 CHANGELOG 写迁移说明。
- 纯文案调整升次版本；修 bug 升修订号。

## 改动流程

1. 拉最新 main，开分支：fix/xxx 或 feat/xxx。
2. 改内容；涉及模板时同步改 assets、references、check 规则。
3. 跑自检：

```bash
python3 -c "compile(open('scripts/manage_archive.py').read(),'x','exec')"
python3 scripts/manage_archive.py --root /tmp/distill-demo init --platform 抖音 --blogger-name demo
python3 scripts/manage_archive.py --root /tmp/distill-demo render
python3 scripts/manage_archive.py --root /tmp/distill-demo check   # 预期 FAIL
```

4. 更新 CHANGELOG.md。
5. 提交，PR 描述里写：改了什么、为什么、对学员有什么影响。
6. 合并即可，软链自动指向新内容，不需要再同步。

## 两个 Agent 的分工

- 谁改谁记录：同一次改动由发起方写 CHANGELOG，不留给对方补。
- 冲突以 Git 为准：只有一个工作目录，冲突在提交层解决。
- 不并发改同一文件：先看最近一次提交，必要时在 PR 里说明。
- 对外说法统一：学员问题以 README 和 SKILL.md 为准，不在对话里承诺未实现的功能。

## 兼容性红线

- 新版本必须能读旧版 蒸馏报告.md；字段缺失时给默认值，不直接报错。
- 模板新增板块时，check 要能给出「缺哪个板块」的明确提示。
- 不引入第三方 Python 包；只用标准库。
- 路径不用绝对路径；统一走 config.json 或 --root。

## 发布前检查

- [ ] README 的安装步骤在一台干净环境走过。
- [ ] check 对空模板报 FAIL，对完整样例报 OK。
- [ ] HTML 在 Chrome、Safari 打开正常，打印预览不溢出。
- [ ] 四条指令单独贴进 ChatGPT／DeepSeek 能正常执行。
- [ ] CHANGELOG 与 version 一致。
