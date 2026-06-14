from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SkillMetadata:
    name: str
    description: str
    author: str = ""
    tags: list[str] = field(default_factory=list)
    version: str = "1.0"


@dataclass
class Skill:
    metadata: SkillMetadata
    content: str
    source: Path | None = None

    def summary(self) -> str:
        tags_str = ", ".join(self.metadata.tags) if self.metadata.tags else "none"
        return f"- **{self.metadata.name}**: {self.metadata.description} (tags: {tags_str})"
