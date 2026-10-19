"""Portal and repository contracts; skill packages live in the canonical workbench."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = "https://github.com/bhumiwitchayasig-bit/grvis-research-workbench"


class RepositoryTests(unittest.TestCase):
    def test_taskplanner_version_and_files(self):
        config = json.loads((ROOT / ".tasks/config.json").read_text(encoding="utf-8"))
        self.assertEqual(config["taskplannerVersion"], "2.1.1")
        self.assertEqual(config["version"], 2)
        for filename in config["states"].values():
            self.assertTrue((ROOT / ".tasks" / filename).is_file())

    def test_task_ids_unique_and_counter(self):
        config = json.loads((ROOT / ".tasks/config.json").read_text(encoding="utf-8"))
        ids = []
        for filename in config["states"].values():
            ids.extend(re.findall(r"^## (TASK-\d+):", (ROOT / ".tasks" / filename).read_text(encoding="utf-8"), re.M))
        self.assertEqual(len(ids), 5)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(config["nextId"], 6)

    def test_duplicate_skill_and_workbench_payloads_are_removed(self):
        for path in (
            ROOT / "skills/reverse",
            ROOT / "skills/grvis-reverse-engineering",
            ROOT / "tools/reverse_workbench.py",
            ROOT / "tests/test_reverse_workbench.py",
            ROOT / "tests/fixtures/reverse-evidence.json",
            ROOT / "docs/REVERSE_WORKBENCH.md",
        ):
            self.assertFalse(path.exists(), path)

    def test_portal_points_to_canonical_skills_and_reader(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
        page = (ROOT / "reverse.html").read_text(encoding="utf-8")
        index = json.loads((ROOT / "knowledge-index.json").read_text(encoding="utf-8"))
        for text in (readme, llms, page):
            self.assertIn(CANONICAL, text)
            self.assertNotIn("grvis-knowledge/blob/main/skills/", text)
        self.assertEqual({item["slug"] for item in index["skills"]}, {"find", "reverse"})
        for item in index["skills"]:
            self.assertTrue(item["source_url"].startswith(CANONICAL + "/blob/main/skills/"))
            self.assertTrue(item["package_url"].startswith(CANONICAL + "/tree/main/skills/"))

    def test_retired_bookmark_page_is_a_tombstone(self):
        page = (ROOT / "reverse-engineering.html").read_text(encoding="utf-8")
        self.assertIn("retired duplicate", page)
        self.assertIn(CANONICAL + "/blob/main/skills/reverse/SKILL.md", page)
        self.assertNotIn("Earlier SKILL.md", page)

if __name__ == "__main__":
    unittest.main()
