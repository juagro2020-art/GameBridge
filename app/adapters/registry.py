from typing import Dict, Optional, List
from app.adapters.base import BaseGameAdapter
from app.adapters.lichess import LichessAdapter
from app.adapters.chess_com import ChessComAdapter
from app.adapters.tier_b import TierBMobileGameAdapter

class GameAdapterRegistry:
    def __init__(self):
        self._adapters: Dict[str, BaseGameAdapter] = {}
        self.register_default_adapters()

    def register(self, adapter: BaseGameAdapter):
        self._adapters[adapter.key] = adapter

    def get(self, key: str) -> Optional[BaseGameAdapter]:
        return self._adapters.get(key)

    def list_adapters(self) -> List[BaseGameAdapter]:
        return list(self._adapters.values())

    def register_default_adapters(self):
        self.register(LichessAdapter())
        self.register(ChessComAdapter())
        self.register(TierBMobileGameAdapter())

registry = GameAdapterRegistry()
