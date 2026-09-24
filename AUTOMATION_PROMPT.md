# 自动化实现与维护 / Automation

本仓库使用 [GitHub Actions 工作流](.github/workflows/weekly-top10.yml)自动发布周报，不依赖 ChatGPT 的 Scheduled 页面。  
This repository uses a [GitHub Actions workflow](.github/workflows/weekly-top10.yml) to publish weekly issues. It does not depend on ChatGPT Scheduled.

## 时间 / Schedule

每周日 20:00，时区 `Asia/Shanghai`。GitHub 允许计划任务因负载而延迟启动，实际抓取时间会写进周报。  
Every Sunday at 20:00 in `Asia/Shanghai`. GitHub may delay scheduled starts during periods of high load; the actual capture time appears in each issue.

## 数据与内容 / Data and content

1. 从 [GitHub Trending — this week](https://github.com/trending?since=weekly)读取当周榜单与“stars this week”数据。
2. 按页面顺序验证公开仓库、主要语言、累计 Star 和 GitHub 可识别的开源许可证；无法确认的条目顺延并在周报注明原因。
3. 使用 [Argos Translate](https://github.com/argosopentech/argos-translate) 的离线英中模型翻译仓库简介。机器翻译可能不够自然；技术事实以原仓库为准。
4. 生成 `reports/YYYY-MM-DD.md` 双语周报，以及 `assets/YYYY-MM-DD-top10.svg` 原创信息图；更新首页最新一期和往期目录。每期应恰有 10 个项目。
5. 若榜单结构、仓库数据或翻译模型不可用，工作流会失败且不会提交不完整的周报。

The workflow reads the weekly GitHub Trending list, verifies public repositories and recognized licenses, translates repository descriptions offline, generates a bilingual Markdown issue and an original SVG chart, and updates the README. If source data or translation is unavailable, the run fails without publishing a partial issue.

## 运行与预演 / Running and previewing

- 修改工作流、脚本、依赖或测试后会触发一次**只预演、不发布**的运行。
- 在 GitHub **Actions → Publish GitHub Weekly Top 10 → Run workflow** 手动运行时，`dry_run` 默认开启；关闭它才会发布。正式发布仅允许北京时间周日进行。
- 正常周日计划运行会自动提交到默认分支，使用仓库自带的 `GITHUB_TOKEN`；无需额外 API 密钥。
- 代码位于 [scripts/build_weekly.py](scripts/build_weekly.py)，测试位于 [tests/test_build_weekly.py](tests/test_build_weekly.py)。

Code changes trigger a preview run without publication. Manual runs default to `dry_run`. Scheduled Sunday runs commit with the repository's built-in `GITHUB_TOKEN`.
