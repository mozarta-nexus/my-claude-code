from dataclasses import dataclass


@dataclass
class SkillMetadata:
    name: str
    description: str
    author: str
    tags: list


@dataclass
class Skill:
    metadata: SkillMetadata
    content: str



