"""Build a bilingual, illustrated GitHub Trending weekly digest.

No generated report is written until ten public repositories with recognized
licenses and verifiable weekly-star counts have been collected.
"""

from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


TRENDING_URL = "https://github.com/trending?since=weekly"
GITHUB_API = "https://api.github.com"
ROOT = Path(__file__).resolve().parents[1]
REPO_PATTERN = re.compile(r"^/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/?$")
WEEKLY_PATTERN = re.compile(r"([\d,]+)\s+stars?\s+this\s+week", re.I)
CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")
JAPANESE_PATTERN = re.compile(r"[\u3040-\u30ff]")


@dataclass(frozen=True)
class Candidate:
    full_name: str
    description: str
    weekly_stars: int


@dataclass(frozen=True)
class Project:
    full_name: str
    url: str
    description_en: str
    description_zh: str
    language: str
    license: str
    weekly_stars: int
    total_stars: int


def http_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "User-Agent": "qianting15-weekly-github-top10/1.0",
        }
    )
    token = os.getenv("GITHUB_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def parse_trending(page: str) -> list[Candidate]:
    soup = BeautifulSoup(page, "html.parser")
    candidates: list[Candidate] = []
    seen: set[str] = set()
    for article in soup.select("article.Box-row"):
        link = article.select_one("h2 a[href]")
        if link is None:
            continue
        match = REPO_PATTERN.fullmatch(link.get("href", "").strip())
        if match is None:
            continue
        full_name = f"{match.group(1)}/{match.group(2)}"
        if full_name.lower() in seen:
            continue
        weekly_match = WEEKLY_PATTERN.search(article.get_text(" ", strip=True))
        if weekly_match is None:
            continue
        description_node = article.select_one("p")
        description = description_node.get_text(" ", strip=True) if description_node else ""
        candidates.append(
            Candidate(full_name, description, int(weekly_match.group(1).replace(",", "")))
        )
        seen.add(full_name.lower())
    return candidates


def get_json(session: requests.Session, url: str) -> dict:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_candidates(session: requests.Session) -> list[Candidate]:
    response = session.get(TRENDING_URL, timeout=30)
    response.raise_for_status()
    candidates = parse_trending(response.text)
    if len(candidates) < 10:
        raise RuntimeError(
            f"GitHub Trending yielded only {len(candidates)} rows with weekly-star counts; "
            "the page structure may have changed. Nothing was published."
        )
    return candidates


def install_translation_models(directions: set[tuple[str, str]]) -> None:
    import argostranslate.package

    argostranslate.package.update_package_index()
    packages = argostranslate.package.get_available_packages()
    for source, target in directions:
        match = next(
            (p for p in packages if p.from_code == source and p.to_code == target), None
        )
        if match is None:
            raise RuntimeError(f"Argos Translate model {source}->{target} is unavailable")
        argostranslate.package.install_from_path(match.download())


def translate_descriptions(description: str) -> tuple[str, str]:
    import argostranslate.translate

    if CJK_PATTERN.search(description):
        zh = description
        en = argostranslate.translate.translate(description, "zh", "en")
    else:
        en = description
        zh = argostranslate.translate.translate(description, "en", "zh")
    if not zh.strip() or not en.strip():
        raise RuntimeError("Translation returned empty text")
    return en.strip(), zh.strip()


def source_language(description: str) -> str | None:
    if JAPANESE_PATTERN.search(description):
        return None
    if CJK_PATTERN.search(description):
        return "zh"
    if any(char.isalpha() and not char.isascii() for char in description):
        return None
    return "en"


def fetch_projects(session: requests.Session, candidates: list[Candidate]) -> tuple[list[Project], list[str]]:
    selected: list[tuple[Candidate, dict, str]] = []
    skipped: list[str] = []
    directions: set[tuple[str, str]] = set()
    for candidate in candidates:
        if len(selected) == 10:
            break
        try:
            metadata = get_json(session, f"{GITHUB_API}/repos/{candidate.full_name}")
        except requests.RequestException as exc:
            skipped.append(f"{candidate.full_name}: metadata unavailable ({type(exc).__name__})")
            continue
        license_info = metadata.get("license") or {}
        license_id = license_info.get("spdx_id") or ""
        if metadata.get("private") or metadata.get("archived") or metadata.get("fork"):
            skipped.append(f"{candidate.full_name}: private, archived, or fork")
            continue
        if license_id in ("", "NOASSERTION", "Other"):
            skipped.append(f"{candidate.full_name}: no recognized open-source license")
            continue
        description = (metadata.get("description") or candidate.description).strip()
        if not description or source_language(description) is None:
            skipped.append(f"{candidate.full_name}: description unavailable or unsupported")
            continue
        if not metadata.get("html_url", "").startswith("https://github.com/"):
            skipped.append(f"{candidate.full_name}: unexpected repository URL")
            continue
        selected.append((candidate, metadata, description))
        directions.add(("zh", "en") if source_language(description) == "zh" else ("en", "zh"))
    if len(selected) != 10:
        raise RuntimeError(
            f"Only {len(selected)} eligible repositories found; skipped: " + "; ".join(skipped)
        )
    install_translation_models(directions)
    projects: list[Project] = []
    for candidate, metadata, description in selected:
        en, zh = translate_descriptions(description)
        projects.append(
            Project(
                full_name=candidate.full_name,
                url=metadata["html_url"],
                description_en=en,
                description_zh=zh,
                language=metadata.get("language") or "Unknown",
                license=metadata["license"]["spdx_id"],
                weekly_stars=candidate.weekly_stars,
                total_stars=int(metadata.get("stargazers_count") or 0),
            )
        )
    return projects, skipped


def safe_markdown(value: str) -> str:
    value = html.escape(value, quote=False).replace("|", "\\|")
    return re.sub(r"([\\`*_{}\[\]()#+!])", r"\\\1", value)


def render_svg(projects: list[Project], issue_date: str) -> str:
    max_stars = max(p.weekly_stars for p in projects)
    rows: list[str] = []
    for index, project in enumerate(projects, 1):
        y = 174 + (index - 1) * 67
        label = project.full_name
        if len(label) > 29:
            label = label[:28] + "…"
        width = max(8, round(project.weekly_stars / max_stars * 450))
        rows.append(
            f'<text x="64" y="{y + 22}" fill="#e8f5f1" font-size="20">'
            f'{index:02d}  {html.escape(label)}</text>'
            f'<rect x="650" y="{y}" width="{width}" height="29" rx="7" fill="#62dfbd"/>'
            f'<text x="1129" y="{y + 22}" fill="#e8f5f1" font-size="20" text-anchor="end">'
            f'+{project.weekly_stars:,}</text>'
        )
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="920" '
            'viewBox="0 0 1200 920" role="img" aria-labelledby="title desc">',
            f'<title id="title">GitHub Weekly Top 10 / GitHub 本周热门开源项目十选 {issue_date}</title>',
            '<desc id="desc">Weekly star gains for ten repositories on GitHub Trending.</desc>',
            '<rect width="1200" height="920" rx="28" fill="#102333"/>',
            '<text x="64" y="70" fill="#62dfbd" font-size="27" font-weight="bold">'
            'GITHUB WEEKLY TOP 10 / 本周热门开源项目十选</text>',
            f'<text x="64" y="112" fill="#adc9c7" font-size="22">{issue_date} · Stars this week / 本周新增 Star</text>',
            '<path d="M64 135H1136" stroke="#426273" stroke-width="2"/>',
            '<g font-family="Arial, Noto Sans CJK SC, sans-serif">',
            *rows,
            '</g>',
            '<path d="M64 856H1136" stroke="#426273" stroke-width="2"/>',
            '<text x="64" y="890" fill="#9bb9b8" font-family="Arial, Noto Sans CJK SC, sans-serif" '
            'font-size="18">Source / 来源: github.com/trending?since=weekly · Snapshot at publication</text>',
            '</svg>',
            '',
        ]
    )


def render_report(projects: list[Project], skipped: list[str], captured: datetime) -> str:
    date = captured.date().isoformat()
    lines = [
        f"# GitHub 本周热门开源项目十选 / GitHub Weekly Open Source Top 10 — {date}",
        "",
        f"![本周项目榜单 / This week's top 10](../assets/{date}-top10.svg)",
        "",
        f"**抓取时间 / Captured:** {captured:%Y-%m-%d %H:%M} Asia/Shanghai  ",
        f"**来源 / Source:** [GitHub Trending — This week]({TRENDING_URL})",
        "",
        "按 GitHub Trending 页面顺序选取，Star 数据为抓取时快照。双语简介按需使用离线机器翻译，请以原项目说明为准。  ",
        "Selected in GitHub Trending page order. Star counts are a capture-time snapshot. Bilingual summaries use offline machine translation where needed; refer to the original repositories for authoritative descriptions.",
        "",
        "| 排名 / Rank | 项目 / Repository | 本周新增 Star / Stars this week | 主要语言 / Language |",
        "| ---: | --- | ---: | --- |",
    ]
    for i, project in enumerate(projects, 1):
        lines.append(
            f"| {i} | [{project.full_name}]({project.url}) | +{project.weekly_stars:,} | "
            f"{safe_markdown(project.language)} |"
        )
    for i, project in enumerate(projects, 1):
        owner = quote(project.full_name.split("/")[0], safe="")
        lines.extend(
            [
                "",
                f"## {i}. [{project.full_name}]({project.url})",
                "",
                f'<img src="https://github.com/{owner}.png?size=80" alt="{owner} avatar" width="56" height="56">',
                "",
                f"**中文简介：** {safe_markdown(project.description_zh)}",
                "",
                f"**English description:** {safe_markdown(project.description_en)}",
                "",
                f"**数据 / Facts:** {safe_markdown(project.language)} · {safe_markdown(project.license)} · "
                f"本周新增 / Weekly +{project.weekly_stars:,} ⭐ · 累计 / Total {project.total_stars:,} ⭐",
            ]
        )
    if skipped:
        lines.extend(
            [
                "",
                "## 顺延说明 / Skipped entries",
                "",
                "以下榜单条目因无法确认开源许可或数据而顺延。 / These entries were skipped because their open-source status or data could not be verified.",
                "",
                *[f"- {safe_markdown(item)}" for item in skipped],
            ]
        )
    return "\n".join(lines) + "\n"


def replace_block(document: str, name: str, body: str) -> str:
    start = f"<!-- {name}_START -->"
    end = f"<!-- {name}_END -->"
    if document.count(start) != 1 or document.count(end) != 1:
        raise RuntimeError(f"README markers for {name} are missing or duplicated")
    before, rest = document.split(start, 1)
    _, after = rest.split(end, 1)
    return before + start + "\n" + body.rstrip() + "\n" + end + after


def update_readme(readme: str, issue_date: str) -> str:
    reports_dir = ROOT / "reports"
    dates = {issue_date}
    if reports_dir.exists():
        dates.update(p.stem for p in reports_dir.glob("????-??-??.md"))
    ordered = sorted(dates, reverse=True)
    latest = f"[{ordered[0]} 周报 / Weekly issue](reports/{ordered[0]}.md)"
    archive = "\n".join(f"- [{d}](reports/{d}.md)" for d in ordered)
    return replace_block(replace_block(readme, "LATEST_ISSUE", latest), "ARCHIVE", archive)


def main() -> None:
    captured = datetime.now(ZoneInfo("Asia/Shanghai"))
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    if captured.weekday() != 6 and not dry_run:
        raise RuntimeError("Publication is limited to Sunday in Asia/Shanghai")
    session = http_session()
    candidates = fetch_candidates(session)
    projects, skipped = fetch_projects(session, candidates)
    date = captured.date().isoformat()
    report = render_report(projects, skipped, captured)
    svg = render_svg(projects, date)
    if dry_run:
        print(f"Dry run: {len(projects)} projects; {len(skipped)} skipped; {len(report)} report characters")
        return
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    updated_readme = update_readme(readme, date)
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / f"{date}-top10.svg").write_text(svg, encoding="utf-8")
    (ROOT / "reports" / f"{date}.md").write_text(report, encoding="utf-8")
    readme_path.write_text(updated_readme, encoding="utf-8")
    print(f"Built {date} report with exactly {len(projects)} projects")


if __name__ == "__main__":
    main()

