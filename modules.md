Voici la synthèse, par bloc :

## Orchestrateur

- **src/urdu_exec_bot/app.py** — boucle principale : lecture incrémentale du CSV, parsing, décision d’ordres, exécution via API, application du risque, persistance d’état.

## I/O & Parsing

- **src/urdu_exec_bot/csv_watcher.py** — tail sécurisé du `signals.csv` avec offset (idempotence).
- **src/urdu_exec_bot/parsers/signal_csv.py** — extraction `instrument`, `action (buy/sell)`, `position_cible (-1/0/+1)` depuis `raw`.

## Modèles

- **models/signal.py** — DTO Signal + enum `SignalAction`.
- **models/order.py** — DTO Order + enums `OrderSide`, `OrderType` internes.
- **models/position.py** — Position et enum `PositionSide`.
- **models/trade_state.py** — état global : positions par instrument, PnL jour, flags de trading (halt évaluation, reset key).

## Services (métier)

- **services/strategy_engine.py** — logique URDU par instrument (−1 close all instrument, 0 buy/sell pour revenir flat, +1 ajoute 1 lot).
- **services/position_manager.py** — calcule les ordres delta (close/open dans le bon sens).
- **services/lot_sizing.py** — lecture des lots fixes par instrument (`instruments_lots.yaml`).
- **services/risk_manager.py** — seuil PnL jour + **mode évaluation** (plafond de gain, halt jusqu’au reset).
- **services/execution_service.py** — envoie les ordres simples (pas de bracket), close-all, séquencement.
- **services/state_store.py** — sérialisation/chargement de `TradeState`.
- **services/topstepx_client.py** — client API TopstepX/ProjectX : `loginKey` → token, `validate`, `order_place`, `search*`, mapping `TSOrderType`/`TSSide`, résolution `contractId` via config.

## Utilitaires

- **utils/time_utils.py** — gestion de la journée de trading (reset local), timestamps.
- **utils/logging_setup.py** — configuration logging depuis YAML.

## Configuration

- **config/settings.yaml** — chemins, CSV, endpoints TopstepX, `contracts` (UB1!→contractId), options d’exécution.
- **config/instruments_lots.yaml** — lots fixes par instrument (défaut = 1).
- **config/risk.yaml** — seuil PnL, mode évaluation (enabled, daily_max_gain, reset).
- **config/logging.yaml** — formatteurs/handlers.

## Scripts

- **scripts/validate_setup.py** — vérifications de setup + tests API live : `loginKey`, `validate`, `account/positions/orders/contracts`.
- **scripts/test_place_order.py** — test manuel de placement d’ordre (dry-run par défaut, `--live` pour envoyer).

## Tests

- **tests/unit/** — stratégie, risk manager, parser, execution service.
- **tests/integration/** — client TopstepX (mock) et pipeline.
- **tests/live/** (optionnel) — endpoints réels si activé.

## Données & État

- **data/input/signals.csv** — flux `received_at,content_type,raw`.
- **state/** — état persistant (positions, PnL, offsets).
- **logs/** — journaux d’exécution.

## Docker & Méta

- **docker/** — `Dockerfile`, `docker-compose.yml`.
- **.env / .env.example** — `TOPSTEPX_API_KEY`, `SETTINGS_PATH`.
- **pyproject.toml / Makefile / README.md** — métadonnées, commandes, doc.
