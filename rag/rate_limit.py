"""Rate limiting basique pour l'API permis bateau (Dokploy).

Fenêtre glissante en mémoire, par adresse IP, thread-safe (lock).
Suffisant pour un VPS personnel — à remplacer par Redis si plusieurs
instances ou si le trafic dépasse la capacité d'un seul processus.

Config (variables d'environnement) :
  RATE_LIMIT_MAX     — requêtes autorisées par fenêtre (défaut 15)
  RATE_LIMIT_WINDOW  — fenêtre en secondes (défaut 60)
"""
import os
import threading
import time
from collections import defaultdict, deque


def _env_int(name: str, default: int) -> int:
    """Lit une variable d'env entière, retombe sur `default` si absente ou invalide."""
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


class RateLimiter:
    def __init__(self, max_requests: int | None = None, window_s: int | None = None):
        self.max_requests = max_requests or _env_int("RATE_LIMIT_MAX", 15)
        self.window_s = window_s or _env_int("RATE_LIMIT_WINDOW", 60)
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, now: float) -> None:
        """Supprime les entrées plus vieilles que la fenêtre (évite les fuites)."""
        expired = [ip for ip, q in self._hits.items() if not q or now - q[-1] > self.window_s]
        for ip in expired:
            del self._hits[ip]

    def allow(self, key: str) -> bool:
        """Retourne True si la requête est autorisée pour `key`, False sinon."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self.window_s:
                q.popleft()
            if len(q) >= self.max_requests:
                return False
            q.append(now)
            self._prune(now)
            return True
