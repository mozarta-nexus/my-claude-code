from pathlib import Path

import yaml

from agent.tools.skills.data import Skill, SkillMetadata


def _parse_skill(text: str) -> tuple[SkillMetadata | None, str]:
    if not text.startswith("---"):
        return None, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text

    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None, text

    if not isinstance(meta, dict):
        return None, text

    metadata = SkillMetadata(
        name=meta.get("name", ""),
        description=meta.get("description", ""),
        author=meta.get("author", ""),
        tags=meta.get("tags", []),
        version=meta.get("version", "1.0"),
    )
    content = parts[2].strip()
    return metadata, content


class SkillsManager:
    def __init__(self, skills_dir: str | None = None):
        self.skills_dir = Path(skills_dir) if skills_dir else None
        self.skills: dict[str, Skill] = {}
        self._load_errors: list[str] = []
        self._load_skills()

    def _load_skills(self):
        if not self.skills_dir or not self.skills_dir.exists():
            return

        skill_files = list(self.skills_dir.glob("**/SKILL.md"))
        if not skill_files:
            return

        for skill_file in skill_files:
            try:
                text = skill_file.read_text(encoding="utf-8")
            except OSError as e:
                self._load_errors.append(f"Failed to read {skill_file}: {e}")
                continue

            metadata, content = _parse_skill(text)
            if metadata is None or not metadata.name:
                self._load_errors.append(f"Invalid SKILL.md: {skill_file}")
                continue

            if metadata.name in self.skills:
                print(
                    f"[Skills] Warning: skill '{metadata.name}' already loaded, overwriting"
                )

            skill = Skill(metadata=metadata, content=content, source=skill_file)
            self.skills[metadata.name] = skill

        print(f"[Skills] Loaded {len(self.skills)} .skills")

    def get(self, name: str) -> Skill | None:
        return self.skills.get(name)

    def list_skills(self) -> list[Skill]:
        return list(self.skills.values())

    def format_summaries(self) -> str:
        if not self.skills:
            return ""

        lines = ["## Available Skills", ""]
        lines.append("你可以通过 `load_skill` 工具加载以下技能，获取详细的操作指令：")
        lines.append("")
        for skill in self.skills.values():
            lines.append(skill.summary())
        return "\n".join(lines)
