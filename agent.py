import os
import shlex
from dataclasses import dataclass
from typing import Callable

from minisweagent import Environment, Model
from minisweagent.agents.default import AgentConfig


@dataclass
class OpenAIModelConfig:
    model_name: str


class OpenAIModel(Model):
    config: OpenAIModelConfig
    cost: float = 0
    n_calls: int = 0

    def __init__(self, model_name: str, **kwargs) -> None:
        self.base_url = kwargs.get("base_url")
        self.api_key = kwargs.get("api_key")
        self.config = OpenAIModelConfig(model_name)

    def query(self, messages: list[dict[str, str]], **kwargs) -> dict:
        raise NotImplementedError("This class is a placeholder only.")


class QwenCodeAgent:
    def __init__(self, model: OpenAIModel, env: Environment, *, config_class: Callable = AgentConfig, **kwargs):
        self.config = config_class(**kwargs)
        self.messages: list[dict] = []
        self.model = model  # type: ignore
        self.model_name = model.config.model_name
        self.env = env

        if self.model.base_url is not None:
            self.base_url = self.model.base_url
        elif "OPENAI_BASE_URL" in os.environ:
            self.base_url = os.environ["OPENAI_BASE_URL"]
        else:
            raise ValueError("No API base url provided.")

        if self.model.api_key is not None:
            self.api_key = self.model.api_key
        elif "OPENAI_API_KEY" in os.environ:
            self.api_key = os.environ["OPENAI_API_KEY"]
        else:
            raise ValueError("No API key provided.")

    def run(self, task: str) -> tuple[str, str]:
        cmd = [
            f'OPENAI_MODEL="{self.model_name}"',
            f'OPENAI_BASE_URL="{self.base_url}"',
            f'OPENAI_API_KEY="{self.api_key}"',
            "qwen",
            "-p",
            shlex.quote(f"Please solve this issue: {task}\n\nAutomatically commit all changes made."),
            "-y",
            "--openai-logging",
        ]
        self.env.execute(" ".join(cmd), cwd="/testbed")
        output = self.env.execute("git diff", cwd="/testbed")
        return "Submitted", output["output"]
