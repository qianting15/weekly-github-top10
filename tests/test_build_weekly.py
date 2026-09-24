import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_weekly import Project, parse_trending, render_svg, replace_block  # noqa: E402


class WeeklyDigestTests(unittest.TestCase):
    def test_trending_rows_keep_order_and_weekly_star_values(self):
        page = """
        <article class="Box-row"><h2><a href="/first/repo">first/repo</a></h2>
          <p>First project</p><span>1,234 stars this week</span></article>
        <article class="Box-row"><h2><a href="/second/tool">second/tool</a></h2>
          <p>Second project</p><span>87 stars this week</span></article>
        <article class="Box-row"><h2><a href="/first/repo">duplicate</a></h2>
          <span>999 stars this week</span></article>
        """
        rows = parse_trending(page)
        self.assertEqual([r.full_name for r in rows], ["first/repo", "second/tool"])
        self.assertEqual([r.weekly_stars for r in rows], [1234, 87])

    def test_svg_is_valid_xml_and_escapes_names(self):
        item = Project("a/repo&tool", "https://github.com/a/repo", "A", "甲", "Python", "MIT", 12, 50)
        svg = render_svg([item], "2026-09-27")
        ET.fromstring(svg)
        self.assertIn("repo&amp;tool", svg)

    def test_readme_block_replacement_keeps_markers(self):
        before = "header\n<!-- ARCHIVE_START -->\nold\n<!-- ARCHIVE_END -->\nfooter"
        after = replace_block(before, "ARCHIVE", "- [2026-09-27](reports/2026-09-27.md)")
        self.assertIn("<!-- ARCHIVE_START -->", after)
        self.assertIn("<!-- ARCHIVE_END -->", after)
        self.assertNotIn("old", after)
        self.assertTrue(after.endswith("footer"))


if __name__ == "__main__":
    unittest.main()

