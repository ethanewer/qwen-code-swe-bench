import json
import os
import platform
import subprocess
from dataclasses import asdict, dataclass
from typing import Any, Callable

from jinja2 import Template
from minisweagent import Environment
from minisweagent.agents.default import AgentConfig, LimitsExceeded, Submitted
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionMessageToolCall
from openai_function_calling import FunctionInferrer


@dataclass
class OpenAIModelConfig:
    model_name: str


class OpenAIModel:
    config: OpenAIModelConfig
    cost: float = 0
    n_calls: int = 0
    n_prompt_tokens: int = 0
    n_completion_tokens: int = 0

    def __init__(self, model_name: str, **kwargs) -> None:
        self.client = OpenAI(base_url=kwargs.get("base_url"), api_key=kwargs.get("api_key"))
        self.config = OpenAIModelConfig(model_name)
        self.sampling_kwargs = {k: v for k, v in kwargs.items() if k not in ["base_url", "api_key"]}

    def query(self, messages: list[dict[str, str]], tools: list[dict[str, Any]]) -> ChatCompletionMessage:
        response: ChatCompletion = self.client.chat.completions.create(
            model=self.config.model_name,
            messages=messages,  # type: ignore
            tools=tools,  # type: ignore
            **self.sampling_kwargs,
        )

        self.n_calls += 1
        if response.usage is not None:
            self.n_prompt_tokens += response.usage.prompt_tokens
            self.n_completion_tokens += response.usage.completion_tokens
            print(f"{response.usage.prompt_tokens=}")

        return response.choices[0].message


class OpenaiBashAgent:
    def __init__(self, model: OpenAIModel, env: Environment, *, config_class: Callable = AgentConfig, **kwargs):
        self.config = config_class(**kwargs)
        self.messages: list[dict] = []
        self.tools: list[dict[str, Any]] = []
        self.functions: dict[str, Callable] = {}
        self.model = model  # type: ignore
        self.env = env

        def execute_bash_command(bash_command: str) -> str:
            """Executes `bash_command` in the terminal and returns all outputs."""
            try:
                output = self.env.execute(bash_command)
                return self.render_template(self.config.action_observation_template, output=output)
            except subprocess.TimeoutExpired as e:
                output = e.output.decode("utf-8", errors="replace") if e.output else ""
                return self.render_template(self.config.timeout_template, action={"action": bash_command}, output=output)
            except TimeoutError:
                return self.render_template(self.config.timeout_template, action={"action": bash_command}, output="")

        function_schema = FunctionInferrer.infer_from_function_reference(execute_bash_command).to_json_schema()
        self.functions[function_schema["name"]] = execute_bash_command
        self.tools.append({"type": "function", "function": function_schema})

    def render_template(self, template: str, **kwargs) -> str:
        cs = asdict(self.config) | asdict(self.env.config) | asdict(self.model.config) | platform.uname()._asdict()
        return Template(template).render(**kwargs, **cs, **os.environ)

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def call_tool(self, tool_call: ChatCompletionMessageToolCall) -> dict[str, str]:
        name = tool_call.function.name
        if name in self.functions:
            try:
                content = self.functions[name](**json.loads(tool_call.function.arguments))
            except Exception as e:
                content = str(e)
        else:
            content = f"`{name}` is not a valid function name."

        return {"role": "tool", "tool_call_id": tool_call.id, "name": name, "content": content}

    def step(self) -> None:
        if 0 < self.config.step_limit <= self.model.n_calls or 0 < self.config.cost_limit <= self.model.cost:
            raise LimitsExceeded()

        message = self.model.query(self.messages, tools=self.tools)
        self.messages.append(message.model_dump())
        tool_calls = message.tool_calls
        if not tool_calls:
            raise Submitted(self.messages[-1]["content"])

        for tool_call in tool_calls:
            self.messages.append(self.call_tool(tool_call))

    def run(self, task: str) -> tuple[str, str]:
        self.messages = [
            {"role": "system", "content": self.config.system_template},
            {"role": "user", "content": self.render_template(self.config.instance_template, task=task)},
        ]
        while True:
            try:
                self.step()
            except Exception as e:
                return type(e).__name__, str(e)
