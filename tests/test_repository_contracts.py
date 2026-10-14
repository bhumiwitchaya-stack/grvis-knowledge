"""Repository and skill metadata checks on the actual checkout."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RepositoryTests(unittest.TestCase):
    def test_taskplanner_version_and_files(self):
        config = json.loads((ROOT / ".tasks/config.json").read_text())
        self.assertEqual(config["taskplannerVersion"], "2.1.1")
        self.assertEqual(config["version"], 2)
        for filename in config["states"].values():
            self.assertTrue((ROOT / ".tasks" / filename).is_file())

    def test_task_ids_unique_and_counter(self):
        config = json.loads((ROOT / ".tasks/config.json").read_text())
        ids = []
        for filename in config["states"].values():
            ids.extend(re.findall(r"^## (TASK-\d+):", (ROOT / ".tasks" / filename).read_text(), re.M))
        self.assertEqual(len(ids), 4)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(config["nextId"], 5)

    def test_skill_frontmatter_and_budget(self):
        content = (ROOT / "skills/reverse/SKILL.md").read_text()
        front = content.split("---", 2)[1]
        self.assertEqual(re.findall(r"^([a-z_]+):", front, re.M), ["name", "description"])
        self.assertIn("name: reverse", front)
        self.assertLess(len(content.splitlines()), 500)

    def test_skill_relative_references(self):
        folder = ROOT / "skills/reverse"
        for path in [folder / "SKILL.md", *folder.glob("references/*.md")]:
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
                if target.startswith(("http:", "https:", "#", "mailto:")):
                    continue
                self.assertTrue((path.parent / target.split("#", 1)[0]).exists(), (path, target))

    def test_no_extra_skill_frontmatter(self):
        content = (ROOT / "skills/reverse/SKILL.md").read_text()
        self.assertTrue(content.startswith("---\nname: reverse\n"))
        self.assertIn("references/rea-workflow.md", content)

    def test_metadata_prompt_and_length(self):
        text = (ROOT / "skills/reverse/agents/openai.yaml").read_text()
        self.assertIn("$reverse", text)
        description = re.search(r'short_description: "([^"]+)"', text).group(1)
        self.assertTrue(25 <= len(description) <= 64)

if __name__ == "__main__":
    unittest.main()
