import time
import requests
import json

from .exceptions import ExternalException
from .llm_client import LLMClient
from .response_utils import get_gemini_response_format
from .prompt_config import PromptConfig


class GeminiClient(LLMClient):
    SERVICE_NAME = "Google Gemini"
    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, prompt_config: PromptConfig):
        super(LLMClient, self).__init__()
        self._prompt_config = prompt_config
        self.debug = False
        self.next_request_time = 0
        self.max_retries = 5

    @property
    def prompt_config(self) -> PromptConfig:
        return self._prompt_config

    def call(self, prompts: list[str]) -> dict:
        if not prompts:
            raise Exception("Empty list of prompts given")

        # Gemini API endpoint
        url = self.get_url()

        headers = {
            "Content-Type": "application/json",
        }

        # Add API key as query parameter (Gemini's preferred method)
        params = {"key": self.prompt_config.api_key}

        user_input = "\n\n".join(prompts)

        if self.debug:
            print(f"Content String: {user_input}\n")
            print(f"System Prompt: {self.prompt_config.system_prompt}\n")

        contents = [{"role": "user", "parts": [{"text": user_input}]}]

        data = {
            "contents": contents,
            "generationConfig": get_gemini_response_format(
                self.prompt_config.response_keys
            ),
        }
        data["generationConfig"]["maxOutputTokens"] = 5120

        # Add system instruction if available
        if (
            hasattr(self.prompt_config, "system_prompt")
            and self.prompt_config.system_prompt
        ):
            system_instruction = {"parts": [{"text": self.prompt_config.system_prompt}]}
            data["systemInstruction"] = system_instruction

        for i in range(self.max_retries):
            self.wait_if_needed()
            try:
                response = requests.post(
                    url, headers=headers, params=params, json=data, timeout=30
                )
            except requests.exceptions.ConnectionError as exc:
                raise ExternalException(
                    f"ConnectionError, could not access the {GeminiClient.SERVICE_NAME} "
                    "service.\nAre you sure you have an internet connection?"
                ) from exc
            try:
                response.raise_for_status()
                self.next_request_time = 0
                return self.parse_json_response(response=response.json())
            except requests.exceptions.HTTPError as exc:
                if response.status_code == 401:
                    raise ExternalException(
                        'Received an "Unauthorized" response; your API key is probably '
                        "invalid."
                    ) from exc
                if response.status_code == 429:
                    retry_after_time = 4 * (2**i)
                    self.next_request_time = time.time() + retry_after_time + 0.5
                    if i == self.max_retries - 1:
                        raise ExternalException(
                            'Received a "429 Client Error: Too Many Requests" response. '
                            f"And did not succeed after {self.max_retries} retries."
                            "The Gemini error is:"
                            f"{response.status_code} {response.reason}\n{response.text}"
                        ) from exc
                if response.status_code == 400:
                    error_details = response.json().get("error", {})
                    error_message = error_details.get("message", "Bad Request")
                    raise ExternalException(
                        f"Bad Request (400): {error_message}\n"
                        "This might be due to invalid model name, malformed request, or unsupported features."
                    ) from exc
                raise ExternalException(
                    f"Error: {response.status_code} {response.reason}\n{response.text}"
                ) from exc
        raise ExternalException("Code is unreachable.")

    def get_url(self) -> str:
        base_url = (self.prompt_config.base_url or "").strip()
        if not base_url:
            base_url = GeminiClient.DEFAULT_BASE_URL

        if ":generateContent" in base_url:
            return base_url

        base_url = base_url.rstrip("/")

        if "/models/" in base_url and not base_url.endswith("/models"):
            return f"{base_url}:generateContent"

        if not base_url.endswith("/models"):
            base_url = f"{base_url}/models"

        return f"{base_url}/{self.prompt_config.model}:generateContent"

    def wait_if_needed(self):
        """Wait until the global `next_request_time` allows a new request."""
        now = time.time()
        if now < self.next_request_time:
            wait_time = self.next_request_time - now
            print(f"Waiting {wait_time:.2f} seconds before the next request.")
            time.sleep(wait_time)

    def parse_json_response(self, response) -> dict:
        if self.debug:
            print(f"Full response: {json.dumps(response, indent=2)}")

        if not response or "candidates" not in response or not response["candidates"]:
            raise ExternalException("Gemini API response is missing 'candidates'.")

        candidate = response["candidates"][0]
        if (
            "content" not in candidate
            or "parts" not in candidate["content"]
            or not candidate["content"]["parts"]
        ):
            raise ExternalException(
                "Gemini API response candidate is missing 'content' or 'parts'."
            )

        message_content = candidate["content"]["parts"][0].get("text")
        try:
            return json.loads(message_content)
        except json.JSONDecodeError as exc:
            raise ExternalException(
                f"Failed to parse JSON from Gemini response: {exc}. Raw content: {message_content}"
            ) from exc
