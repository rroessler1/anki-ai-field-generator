import json
import time
import requests

from .exceptions import ExternalException
from .llm_client import LLMClient
from .response_utils import get_openai_response_format
from .prompt_config import PromptConfig


class OpenAIClient(LLMClient):
    DEFAULT_URL = "https://api.openai.com/v1/chat/completions"
    SERVICE_NAME = "OpenAI"

    def __init__(self, prompt_config: PromptConfig):
        super(LLMClient, self).__init__()
        self._prompt_config = prompt_config
        self.debug = False
        self.next_request_time = 0
        self.retry_after_time = 0

    @property
    def prompt_config(self) -> PromptConfig:
        return self._prompt_config

    def call(self, prompts: list[str]) -> dict:
        if not prompts:
            raise Exception("Empty list of prompts given")
        url = self.get_url()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.prompt_config.api_key}",
        }
        # This supports multiple prompts (newline-separated) if we switch back to batch processing.
        user_input = "\n\n".join(prompts)
        if self.debug:
            print(f"Content String: {user_input}\n")
            print(f"System Prompt: {self.prompt_config.system_prompt}\n")
        data = {
            "model": self.prompt_config.model,
            "messages": [
                {"role": "user", "content": user_input},
            ],
            "response_format": get_openai_response_format(
                self.prompt_config.response_keys
            ),
        }
        if not self.prompt_config.model.startswith("o"):
            data["messages"].insert(
                0, {"role": "system", "content": self.prompt_config.system_prompt}
            )

        self.wait_if_needed()

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
        except requests.exceptions.ConnectionError as exc:
            raise ExternalException(
                f"ConnectionError, could not access the {OpenAIClient.SERVICE_NAME} "
                "service.\nAre you sure you have an internet connection?"
            ) from exc

        try:
            response.raise_for_status()
            self.next_request_time = time.time() + self.retry_after_time + 0.5
        except requests.exceptions.HTTPError as exc:
            if response.status_code == 401:
                raise ExternalException(
                    'Received an "Unauthorized" response; your API key is probably invalid.'
                ) from exc
            if response.status_code == 429:
                self.retry_after_time = int(response.headers.get("Retry-After", 20))
                self.next_request_time = time.time() + self.retry_after_time + 1
                raise ExternalException(
                    'Received a "429 Client Error: Too Many Requests" response. '
                    "On the lowest tier, you are rate limited to 3 requests per "
                    "minute. We will start sending one request every "
                    f"{self.retry_after_time} seconds.\n\n<br/><br/>"
                    f"<b>OpenAI Error:</b> {response.text}"
                ) from exc
            raise ExternalException(
                f"Error: {response.status_code} {response.reason}\n{response.text}"
            ) from exc

        return self.parse_json_response(response=response.json())

    def get_url(self) -> str:
        base_url = (self.prompt_config.base_url or "").strip()
        if not base_url:
            return OpenAIClient.DEFAULT_URL

        if "chat/completions" not in base_url:
            if not base_url.endswith("/"):
                base_url += "/"
            base_url += "chat/completions"
        return base_url

    def wait_if_needed(self):
        """Wait until the global `next_request_time` allows a new request."""
        now = time.time()
        if now < self.next_request_time:
            wait_time = self.next_request_time - now
            print(f"Waiting {wait_time:.2f} seconds before the next request.")
            time.sleep(wait_time)

    def parse_json_response(self, response) -> dict:
        message_content = response["choices"][0]["message"]["content"]
        results = json.loads(message_content)
        if self.debug:
            print(f"Results: {results}")
        return results
