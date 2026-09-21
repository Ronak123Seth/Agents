import os
import json
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_env_file(path=".env"):
    env_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(env_path):
        return

    with open(env_path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip("\"'"))

load_env_file()
api_key = os.environ.get("API_KEY")
if not api_key:
    raise RuntimeError("API_KEY is missing from .env or the environment")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
)

class Agent:
    def __init__(self, name, role, model="openai/gpt-oss-20b", toolkit=None):
        self.name = name
        self.role = role
        self.model = model
        self.toolkit = toolkit

    def invoke(self, instruction):
        input_text = f"You are a {self.name}.\n\n Role: {self.role}\n\nInstruction: {instruction}"
        input_items = [{"role": "user", "content": input_text}]
        tool_schemas = [
            {key: value for key, value in tool.items() if key != "handler"}
            for tool in (self.toolkit or [])
        ]
        tool_handlers = {
            tool["name"]: tool["handler"]
            for tool in (self.toolkit or [])
        }

        for _ in range(10):
            response = client.responses.create(
                input=input_items,
                model=self.model,
                tools=tool_schemas or None,
            )
            tool_calls = [
                item for item in response.output
                if item.type == "function_call"
            ]
            if not tool_calls:
                return response.output_text

            input_items += response.output
            for tool_call in tool_calls:
                handler = tool_handlers.get(tool_call.name)
                if handler is None:
                    raise RuntimeError(f"Unknown tool requested: {tool_call.name}")

                arguments = json.loads(tool_call.arguments)
                result = handler(**arguments)
                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": json.dumps(result),
                    }
                )

        raise RuntimeError("The model requested too many tool calls")