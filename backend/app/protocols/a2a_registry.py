from __future__ import annotations

import json
from pathlib import Path

from fastapi import HTTPException, status

from ..core.schemas import A2AAgentCard


class A2ARegistry:
    def __init__(self) -> None:
        self._cards_dir = self._discover_cards_dir()

    def list_cards(self) -> list[A2AAgentCard]:
        cards = []
        for path in sorted(self._cards_dir.glob("*.json")):
            cards.append(A2AAgentCard.model_validate(json.loads(path.read_text(encoding="utf-8"))))
        return cards

    def get_card(self, card_id: str) -> A2AAgentCard:
        for card in self.list_cards():
            if card.card_id == card_id:
                return card
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="A2A agent card not found.")

    def _discover_cards_dir(self) -> Path:
        current = Path(__file__).resolve().parent
        candidate = current / "agent_cards"
        if candidate.is_dir():
            return candidate
        raise RuntimeError("Unable to locate A2A agent cards directory.")
