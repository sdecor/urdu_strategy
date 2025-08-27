Voici la **checklist de couverture** — qui teste quoi, et comment savoir si tout est bien couvert.

# 📋 Mapping modules → tests

- **utils/config_loader.py**

  - (Indirectement utilisé par `DummyConfig` dans `conftest.py`)
  - ✅ Pas de test direct nécessaire pour ce jalon.

- **utils/log_sanitizer.py**

  - ✅ `tests/test_log_sanitizer.py`

    - `sanitize_headers` masque bien `Authorization`
    - `safe_log_api_call` ne log pas le token brut

- **utils/time_gate.py**

  - ✅ Couvert indirectement par `tests/test_trading_time_and_entry_policy.py` (si tu l’as ajouté)
  - (Sinon, testé implicitement via logique globale dans `main`, pas bloquant)

- **utils/schedule_gate.py** & **strategy/entry_policy.py**

  - ✅ `tests/test_entry_policy.py`

    - Quotas par fenêtre (morning/day), `commit_entry`, refus hors quota

  - (ScheduleGate résolu + EntryPolicy contract de 3 valeurs)

- **utils/schedule_watcher.py**

  - ✅ `tests/test_schedule_watcher.py`

    - `flatten_at_end` déclenché à la fin d’une fenêtre (mock `datetime` + faux executor)

- **orders/order_builder.py**

  - ✅ `tests/test_order_builder.py`

    - Payload MARKET/LIMIT, validations (`size>0`, `limit_price` requis)

- **orders/order_sender.py**

  - ✅ `tests/test_order_sender.py`

    - Normalisation de réponse, gestion d’exception engine

- **fills/fill_resolver.py**

  - ✅ `tests/test_fill_resolver.py`

    - Polling positions jusqu’à trouver `averagePrice`, retries paramétrés

- **strategy/tp_manager.py**

  - ✅ `tests/test_tp_manager.py`

    - Calcul TP long/short (`tick_size=1/32`, `ticks=4`)
    - `override_ticks` (ex: 8 ticks → 117.25)

- **strategy/tp_placer.py**

  - ✅ `tests/test_tp_placer.py`

    - Orchestration : récupère fill → construit payload → envoie LIMIT
    - Cas “pas de fill” → n’envoie rien

- **strategy/schedule_executor.py**

  - ✅ `tests/test_schedule_executor.py`

    - Stratégie A : TP sur tous les lots
    - Stratégie B : TP partiel + carry
    - Vérification payload MARKET + appel TP placer

- **risk/risk_guard.py**

  - ✅ `tests/test_risk_guard.py`

    - `max_order_size` → refus
    - `min_minutes_before_stop` → refus si trop proche du stop
    - Cas OK

- **trading/executor.py**

  - ✅ `tests/test_executor_sim.py`

    - En simulation : MARKET suivi d’un TP LIMIT avec bon prix/side/size

# ✅ Conseils si un test échoue

- **ImportError (module non trouvé)**
  → vérifie les **packages** (dossiers avec `__init__.py`) : `orders/`, `fills/`, `strategy/`, `risk/`, `utils/`, `trading/`.

- **Token visible dans logs (log_sanitizer)**
  → assure-toi que tous les logs d’API passent par `safe_log_api_call` ou `sanitize_headers`.

- **TP price mismatch**
  → check `contracts[contract_id].tick_size` et `strategy.tp.ticks` ou `override_ticks` dans le test.
  → `1/32` doit être parsé en `0.03125`.

- **Schedule tests instables**
  → Les tests fournis monkeypatchent `current_schedule_id` (déterministes). Si tu as modifié le gate, garde ce monkeypatch.

- **Executor (simu) échoue**
  → vérifie `TradeSimulator` : il doit exposer `place_order`, `get_open_positions`, `flatten_all`.
  → La fixture `simulator_spy` patch ces méthodes — garde-la telle quelle.

# ▶️ Exécution recommandée

- Tout lancer :

  ```bash
  pytest -v
  ```

- Ou par fichier pour isoler :

  ```bash
  pytest tests/test_order_builder.py -v
  pytest tests/test_order_sender.py -v
  pytest tests/test_fill_resolver.py -v
  pytest tests/test_tp_manager.py -v
  pytest tests/test_tp_placer.py -v
  pytest tests/test_schedule_executor.py -v
  pytest tests/test_risk_guard.py -v
  pytest tests/test_schedule_watcher.py -v
  pytest tests/test_entry_policy.py -v
  pytest tests/test_executor_sim.py -v
  ```
