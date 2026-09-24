# 每周 GitHub 热门开源项目十选：定时任务说明

**建议任务名 / Suggested task name:** GitHub 本周热门开源项目十选  
**时区 / Time zone:** Asia/Shanghai  
**频率 / Recurrence:** 每周日 20:00；RRULE:FREQ=WEEKLY;BYDAY=SU;BYHOUR=20;BYMINUTE=0  
**发布仓库 / Destination:** https://github.com/qianting15/weekly-github-top10

## 每次运行的指令 / Instructions for every run

现在生成并发布一份 GitHub 本周热门开源项目 Top 10 双语图文周报到 `qianting15/weekly-github-top10`。用户已明确授权每周自动发布。请使用 GitHub 插件读取与写入该仓库，并在完成后返回本期周报链接。

1. 以运行时的北京时间为准，打开 [GitHub Trending 的 weekly 列表](https://github.com/trending?since=weekly)。记录抓取时间（Asia/Shanghai）、页面 URL 和榜单顺序。这里的“本周”指抓取时 GitHub Trending 所展示的最近一周，不要把累计 Star 数误写为本周新增 Star 数。
2. 按榜单顺序挑选前 10 个有效项目：必须是公开、可访问的真实开源仓库；排除广告、重复、已删除仓库和无法确认许可或开源状态的条目，并记录跳过原因。若榜单不足 10 个，说明原因，不得补造项目、数据或排名。
3. 逐一核对项目原始仓库页面和 README。记录仓库全名、原始链接、主要语言、许可、本周新增 Star 数（仅当榜单确实显示）、抓取时累计 Star 数，以及一句准确的用途介绍。不要把仓库作者的宣传语当成已验证的性能或安全事实。无法核实的数字写“未提供 / Not available”。
4. 写一份精炼、可读的中英双语 Markdown 周报。文件路径为 `reports/YYYY-MM-DD.md`，日期使用运行时北京时间的周日日期。报告须包含：标题及日期；来源与抓取时间；一张本期 SVG 数据图；十项排名总览表；每个项目各自的中文介绍和英文介绍、适用场景、原仓库链接、主要语言、许可、可核实的 Star 数据。中英内容表达同样的事实，不要只翻译标题。每个项目可使用原作者的 GitHub 头像作为小图，并以仓库链接标注来源。避免未经许可复制项目截图。
5. 生成 `assets/YYYY-MM-DD-top10.svg`：1200×630 的原创矢量信息图，展示十个项目的名称与 GitHub Trending 显示的本周新增 Star 数。若榜单没有提供可核实的本周新增 Star 数，改用十项排名卡片，不要伪造柱形图数值。SVG 需包含中英文标题、日期、来源说明，文字要清晰，XML 转义正确，GitHub Markdown 可显示。封面图与周报正文中都引用该 SVG。
6. 更新根目录 `README.md`，将 `LATEST_ISSUE_START/END` 标记间的内容替换为本期周报的链接与日期，并在 `ARCHIVE_START/END` 标记间维护按日期倒序排列的往期目录。保留标记以供后续运行使用；其他内容不要覆盖。
7. 写入前检查本期路径是否存在。若存在，核对内容后更新同一期文件，避免重复发布；对同一路径的 GitHub 写入按顺序进行，更新文件时使用最新 blob SHA。先写 SVG，再写周报，最后更新 README。若发布失败，不要声称成功，报告具体失败环节和所需操作。
8. 完成后重新读取已发布的周报与 README，确认恰有 10 个项目、双语介绍完整、SVG 路径有效、链接可打开，并返回本期链接。若是首次运行，提示用户检查图片在 GitHub 页面上的实际显示效果。

## Report skeleton

```markdown
# GitHub 本周热门开源项目十选 / GitHub Weekly Open Source Top 10
日期 / Date: YYYY-MM-DD · 抓取时间 / Captured: YYYY-MM-DD HH:mm Asia/Shanghai

![本期十项可视化 / This week's top 10](../assets/YYYY-MM-DD-top10.svg)

来源 / Source: [GitHub Trending — weekly](https://github.com/trending?since=weekly)

| 排名 / Rank | 项目 / Repository | 本周新增 Star / Stars this week | 主要语言 / Language |
| --- | --- | ---: | --- |
| 1 | [owner/repo](https://github.com/owner/repo) | ... | ... |

## 1. owner/repo
<img src="https://github.com/owner.png?size=80" alt="owner avatar" width="56" height="56">

**中文：** ...
**English:** ...

**适用场景 / Use cases:** 中文…… / English ...
**数据 / Facts:** 主要语言 / Language · 许可 / License · 本周新增 Star / Stars this week · 累计 Star / Total stars
**原项目 / Original repository:** https://github.com/owner/repo

<!-- Repeat for projects 2–10. -->
```

## 质量边界 / Quality boundaries

- 只引用真实项目和当期数据；所有项目链接必须指向原仓库。
- 不要从未经确认的第三方排行榜替换 GitHub Trending weekly。
- 文字、排名、图表数值保持一致；如使用估算或推断，明确标注。
- 不要发布 API 密钥、令牌、私人数据或复制受版权保护的长段文字。
