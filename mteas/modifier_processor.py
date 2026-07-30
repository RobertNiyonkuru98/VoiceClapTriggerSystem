"""Modifier word processing (FR3.x)."""
from __future__ import annotations

from typing import Dict, List, Optional


class ModifierProcessor:
    def __init__(self, categories: Dict[str, List[str]]):
        self.categories = categories

    def classify(self, phrase: Optional[str]) -> Optional[str]:
        phrase = (phrase or "").lower()
        if not phrase:
            return None
        for category, keywords in self.categories.items():
            if any(kw in phrase for kw in keywords):
                return category
        return None
