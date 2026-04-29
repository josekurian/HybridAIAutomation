from typing import Any


class OpenAIClient:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def summarize(self, instructions: str, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("The openai package is not installed.") from exc

        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
        )
        text = getattr(response, "output_text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()

        extracted = self._extract_text(response)
        if not extracted:
            raise RuntimeError("OpenAI response did not contain output text.")
        return extracted

    def _extract_text(self, response: Any) -> str:
        output_items = getattr(response, "output", []) or []
        collected: list[str] = []

        for item in output_items:
            content = getattr(item, "content", []) or []
            for part in content:
                part_type = getattr(part, "type", "")
                if part_type == "output_text":
                    text = getattr(part, "text", "")
                    if text:
                        collected.append(text.strip())

        return "\n".join(fragment for fragment in collected if fragment)
