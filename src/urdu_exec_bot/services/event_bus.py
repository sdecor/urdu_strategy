from collections import defaultdict
from typing import Any, Callable, DefaultDict, List


class EventBus:
    def __init__(self) -> None:
        self._subs: DefaultDict[str, List[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable[[Any], None]) -> Callable[[Any], None]:
        self._subs[event].append(handler)
        return handler

    def publish(self, event: str, payload: Any = None) -> None:
        for h in list(self._subs.get(event, [])):
            try:
                h(payload)
            except Exception:
                pass
