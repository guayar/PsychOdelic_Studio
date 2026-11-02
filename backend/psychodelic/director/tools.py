"""Rejestr narzedzi AI Directora. Kazde narzedzie ma schemat argumentow, poziom uprawnien i walidacje.

Poziomy: READ (zawsze), PREPARE (buduje plan/komende, bez wykonania), EXECUTE (wymaga jawnej zgody
czlowieka, a w tej wersji i tak jest zablokowane przez brak zgody na GPU). Brak shell/sudo/git/SQL.
"""
from dataclasses import dataclass, field
from typing import Callable

READ, PREPARE, EXECUTE, HUMAN_ONLY = "READ", "PREPARE", "EXECUTE", "HUMAN_ONLY"


class ToolError(ValueError):
    pass


@dataclass
class Tool:
    name: str
    level: str
    schema: dict                      # {"field": "type"} z walidacja typow
    handler: Callable = None
    description: str = ""


@dataclass
class ToolRegistry:
    tools: dict = field(default_factory=dict)

    def register(self, tool: Tool):
        if tool.name in self.tools:
            raise ToolError(f"narzedzie juz zarejestrowane: {tool.name}")
        if tool.name.startswith(("shell", "sudo", "git", "sql")):
            raise ToolError("zabronione nazwy narzedzi (shell/sudo/git/sql)")
        self.tools[tool.name] = tool

    def describe(self):
        return [{"name": t.name, "level": t.level, "schema": t.schema, "description": t.description}
                for t in self.tools.values()]

    def validate_args(self, name, args):
        if name not in self.tools:
            raise ToolError(f"nieznane narzedzie: {name}")
        spec = self.tools[name].schema
        extra = set(args) - set(spec)
        if extra:
            raise ToolError(f"nadmiarowe argumenty: {sorted(extra)}")
        for key, typ in spec.items():
            if key not in args:
                raise ToolError(f"brak argumentu: {key}")
            val = args[key]
            ok = {"str": isinstance(val, str), "int": isinstance(val, int) and not isinstance(val, bool),
                  "float": isinstance(val, (int, float)) and not isinstance(val, bool),
                  "list": isinstance(val, list), "dict": isinstance(val, dict), "bool": isinstance(val, bool)}[typ]
            if not ok:
                raise ToolError(f"zly typ argumentu {key}: oczekiwano {typ}")
        return args

    def call(self, name, args, approved_by_human=False):
        tool = self.tools.get(name)
        if tool is None:
            raise ToolError(f"nieznane narzedzie: {name}")
        args = self.validate_args(name, args)
        if tool.level == EXECUTE and not approved_by_human:
            raise ToolError(f"{name}: wymaga zgody czlowieka (EXECUTE)")
        if tool.level == HUMAN_ONLY:
            raise ToolError(f"{name}: tylko czlowiek (np. akceptacja jakosci)")
        return tool.handler(args)
