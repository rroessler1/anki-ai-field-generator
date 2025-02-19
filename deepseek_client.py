import json
import requests

from .exceptions import ExternalException
from .llm_client import LLMClient
from .prompt_config import PromptConfig


class DeepseekClient(LLMClient):
    # TODO: this should be configurable
    MODEL = "deepseek-chat"
    URL = "https://api.deepseek.com/chat/completions"
    SERVICE_NAME = "DeepSeek"

    def __init__(self, prompt_config: PromptConfig):
        super(LLMClient, self).__init__()
        self._prompt_config = prompt_config
        self.debug = False

    @property
    def prompt_config(self) -> PromptConfig:
        return self._prompt_config

    def call(self, prompts: list[str]) -> list[dict]:
        if not prompts:
            raise Exception("Empty list of prompts given")
        url = DeepseekClient.URL
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.prompt_config.api_key}",
        }
        # This supports multiple prompts (newline-separated) if we switch back to batch processing.
        user_input = "\n\n".join(prompts)
        if self.debug:
            print(f"Content String: {user_input}\n")
            print(f"System Prompt: {self.config.system_prompt}\n")
        data = {
            "model": DeepseekClient.MODEL,
            "messages": [
                {"role": "system", "content": self.prompt_config.system_prompt},
                {"role": "user", "content": user_input},
            ],
            "response_format": {"type": "json_object"},
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
        except requests.exceptions.ConnectionError as exc:
            raise ExternalException(
                f"ConnectionError, could not access the {DeepseekClient.SERVICE_NAME} "
                "service.\nAre you sure you have an internet connection?"
            ) from exc

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            if response.status_code == 401:
                raise ExternalException(
                    'Received an "Unauthorized" response; your API key is probably invalid.'
                ) from exc
            if response.status_code == 429:
                raise ExternalException(
                    'Received a "429 Client Error: Too Many Requests" response; you might be rate limited to 3 requests per minute.'
                ) from exc
            raise ExternalException(
                f"Error: {response.status_code} {response.reason}"
            ) from exc

        return self.parse_json_response(
            response=response.json(),
            expected_length=len(prompts),
            user_input=user_input,
        )

    def parse_json_response(
        self, response, expected_length: int, user_input: str = None
    ) -> list[dict]:
        message_content = response["choices"][0]["message"]["content"]
        results = json.loads(message_content)
        if isinstance(results, dict):
            results = [results]
        if len(results) != expected_length:
            print(
                (
                    f"WARNING: Results size of {len(results)} didn't match input length of {expected_length}.\n"
                    "This is normally the model being weird and not doing what you told it to do in the prompt.\n"
                    f'The "content" passed was:\n{user_input}\nand the response was:\n{message_content}'
                )
            )
        if self.debug:
            for i, sentence in enumerate(results):
                print(f"Result {i}: {sentence}")
        return results
