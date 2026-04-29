from typing import Any

import httpx


class OCIAIClient:
    def __init__(self, endpoint: str | None, api_key: str | None, model: str) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model

    def is_configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    def summarize(self, prompt: str) -> str:
        if not self.endpoint or not self.api_key:
            raise RuntimeError("OCI AI endpoint configuration is incomplete.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": prompt,
        }

        response = httpx.post(self.endpoint, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        return self._extract_text(response.json())

    def _extract_text(self, payload: Any) -> str:
        if isinstance(payload, dict):
            for key in ("output_text", "text", "answer", "generated_text", "message"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

            choices = payload.get("choices")
            if isinstance(choices, list):
                for choice in choices:
                    if not isinstance(choice, dict):
                        continue
                    message = choice.get("message")
                    if isinstance(message, dict):
                        content = message.get("content")
                        if isinstance(content, str) and content.strip():
                            return content.strip()
                    text = choice.get("text")
                    if isinstance(text, str) and text.strip():
                        return text.strip()

            output = payload.get("output")
            if isinstance(output, list):
                fragments = []
                for item in output:
                    if isinstance(item, str):
                        fragments.append(item.strip())
                    elif isinstance(item, dict):
                        text = item.get("text")
                        if isinstance(text, str):
                            fragments.append(text.strip())
                joined = "\n".join(fragment for fragment in fragments if fragment)
                if joined:
                    return joined

        raise RuntimeError("OCI AI response did not contain readable text.")
