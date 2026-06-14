from pathlib import Path


class SkillsManager:
    def __init__(self,skills_dir:str|None = "."):
        self.skills_dir = Path(skills_dir)
        self.skills:dict = {}
        self._load_skills()

    def _load_skills(self):
        if not self.skills_dir.exists():
            return

        self.skills_dir.glob("**/SKILL.md")
