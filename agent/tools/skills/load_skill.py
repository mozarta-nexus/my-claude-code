from agent.tools.base import Tool
from agent.tools.skills.skills import SkillsManager


class LoadSkill(Tool):
    def __init__(self, manager: SkillsManager):
        self.manager = manager

    @property
    def name(self) -> str:
        return "load_skill"

    @property
    def description(self) -> str:
        return (
            "加载指定技能的详细操作指令。"
            "当你需要按照专业流程执行任务时，先加载对应的 skill 获取详细指导。"
        )

    @property
    def parameters(self) -> dict:
        skill_names = list(self.manager.skills.keys())
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": f"要加载的技能名称，可选值: {skill_names}",
                },
            },
            "required": ["name"],
        }

    def execute(self, **kwargs) -> str:
        skill_name = kwargs.get("name", "")
        self._print_call(**kwargs)

        skill = self.manager.get(skill_name)
        if not skill:
            available = ", ".join(self.manager.skills.keys())
            result = f"Error: skill '{skill_name}' not found. Available: {available}"
            self._print_result(result)
            return result

        result = f"# Skill: {skill.metadata.name}\n\n{skill.content}"
        self._print_result(result)
        return result
