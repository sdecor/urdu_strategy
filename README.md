README.md

````md
# URDU Exec Bot

Lit un CSV de signaux (`received_at,content_type,raw`) et exécute des **ordres simples** via l’API TopstepX (pas de brackets).  
Stratégie « URDU » multi-instruments (UB1!, GC1!, …) avec gestion du risque (seuil PnL, mode évaluation).

---

## 1) Prérequis

- Python 3.11+
- PowerShell (Windows)
- Accès API TopstepX (clé **API Key** ProjectX, pas un bearer temporaire)
- Optionnel : Docker / Docker Compose

---

## 2) Installation rapide

```powershell
# Cloner / aller dans le dossier
cd .\URDU_bot

# (Optionnel) venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Dépendances
pip install -r requirements-dev.txt
```
````

---

## 3) Configuration

### 3.1 Variables d’environnement

`.env` (copier depuis `.env.example`) :

```env
TOPSTEPX_API_KEY=VOTRE_API_KEY_PROJECTX
SETTINGS_PATH=./config/settings.yaml
```

### 3.2 `config/settings.yaml` (extrait TopstepX + endpoints + contrats)

```yaml
topstepx:
  base_url: https://api.topstepx.com
  username: "invest@artinitiative.net"
  account_id: "9925383"
  auth:
    api_key_env: TOPSTEPX_API_KEY
  endpoints:
    login_key: /api/Auth/loginKey
    validate_token: /api/Auth/validate
    order_search: /api/Order/search
    order_search_open: /api/Order/searchOpen
    order_cancel: /api/Order/cancel
    position_search_open: /api/Position/searchOpen
    contract_available: /api/Contract/available
    contract_search: /api/Contract/search
    contract_search_by_id: /api/Contract/searchById
    order_place: /api/Order/place
    account_search: /api/Account/search
  contracts:
    UB1!: "CON.F.US.ULA.U25"
    GC1!: "REPLACE_ME"
```

Autres fichiers :

- `config/instruments_lots.yaml` – lots fixes :

  ```yaml
  lots:
    default: 1
    UB1!: 1
    GC1!: 1
  ```

- `config/risk.yaml` – risque & mode évaluation :

  ```yaml
  pnl:
    daily_close_all_when_gte: 2000
    currency: USD
    reset_time_local: "00:00"

  evaluation:
    enabled: false
    daily_max_gain_usd: 3000
    reset_time_local: "00:00"

  trading:
    allow_flip_on_exit: true
    unique_trade_at_a_time: true
    max_size_per_instrument: null
    allowed_instruments: ["GC", "GC1!", "UB", "UB1!", "ES", "NQ"]
  ```

---

## 4) Format CSV de signaux

Chemin par défaut : `data/input/signals.csv`
En-tête : `received_at,content_type,raw`

Exemples :

```
2025-08-20T17:32:01.021609Z,text/plain; charset=utf-8,"Urdu Blocks Indicator (...): ordre sell @ 1 effectué sur UB1!. La nouvelle position de la stratégie est -1"
2025-08-20T17:32:01.022832Z,text/plain; charset=utf-8,"Urdu Blocks Indicator (...): ordre sell @ 1 effectué sur UB1!. La nouvelle position de la stratégie est 0"
2025-08-20T17:49:34.098182Z,text/plain; charset=utf-8,"Urdu Blocks Indicator (...): ordre buy @ 1 effectué sur UB1!. La nouvelle position de la stratégie est 0"
2025-08-20T17:49:34.104644Z,text/plain; charset=utf-8,"Urdu Blocks Indicator (...): ordre buy @ 1 effectué sur UB1!. La nouvelle position de la stratégie est 1"
```

Parsing :

- Extraction **instrument** (ex. `UB1!`), **action** (`buy|sell`) et **position_cible** ∈ {−1, 0, +1} depuis `raw`.

---

## 5) Règles d’exécution (URDU)

Par instrument (indépendant) :

- `position_cible = −1` → **fermer toutes** les positions sur l’instrument (close long/short ⇒ FLAT).
- `position_cible = 0` & message **sell** → **SELL 1** (ferme un long ⇒ FLAT).
- `position_cible = 0` & message **buy** → **BUY 1** (ferme un short ⇒ FLAT).
- `position_cible = +1` → **doubler** la position : ajouter **+1 lot** dans le sens courant ; si flat, **ouvrir 1** dans le sens du message (BUY ⇒ long, SELL ⇒ short).

Lots : valeurs fixes par instrument (`config/instruments_lots.yaml`, def = 1).
**Aucun bracket** n’est envoyé : ordres simples uniquement.

---

## 6) Lancer le bot

```powershell
# S’assurer que .env est renseigné
python -u .\src\urdu_exec_bot\app.py
```

Boucle :

- lecture incrémentale du CSV,
- décision d’ordres,
- envoi via TopstepX,
- application du risque (close-all si seuil atteint),
- persistance d’état (`state/`).

---

## 7) Validation du setup

```powershell
# Vérifications fichiers/chemins + Auth loginKey + appels API "safe"
python .\scripts\validate_setup.py

# Sans appels API live
python .\scripts\validate_setup.py --no-api-check

# Sortie JSON + stricte
python .\scripts\validate_setup.py --json --strict
```

Le validateur :

- lit `.env` et `settings.yaml`,
- vérifie `topstepx.username`, `account_id`, endpoints (incl. `validate_token`),
- tente l’auth **loginKey** puis **validate**, puis des endpoints de lecture (positions, ordres ouverts, contrats).

---

## 8) Tester un placement d’ordre (manuel)

```powershell
# Dry-run (aucun envoi)
python .\scripts\test_place_order.py -i UB1! -s BUY

# Live market SELL 1
python .\scripts\test_place_order.py -i UB1! -s SELL --live

# Live limit BUY 1 @ 123.45
python .\scripts\test_place_order.py -i UB1! -s BUY -t LIMIT -p 123.45 --live
```

Le script résout `contractId` via `topstepx.contracts` et place un **ordre simple** (`type/side/size`), sans bracket.

---

## 9) Docker (optionnel)

```powershell
Copy-Item .env.example .env
notepad .env   # renseigner TOPSTEPX_API_KEY
docker compose up --build -d
docker compose logs -f
```

Volumes montés : `config/`, `data/`, `logs/`, `state/`.

---

## 10) Tests

```powershell
pytest -q
```

Tests live (optionnels) avec l’API : utiliser `scripts/validate_setup.py` (recommandé).
(`tests/live/test_topstepx_live_api.py` peut être ajouté/activé au besoin via `LIVE_API_TESTS=1`.)

---

## 11) Arborescence

```
.
├─ config/
│  ├─ settings.yaml
│  ├─ instruments_lots.yaml
│  ├─ risk.yaml
│  └─ logging.yaml
├─ data/
│  └─ input/
│     └─ signals.csv
├─ logs/
├─ scripts/
│  ├─ validate_setup.py
│  └─ test_place_order.py
├─ src/
│  └─ urdu_exec_bot/
│     ├─ app.py
│     ├─ csv_watcher.py
│     ├─ parsers/
│     ├─ services/
│     ├─ models/
│     └─ utils/
├─ state/
│  └─ offsets/
├─ tests/
├─ docker/
├─ .env
├─ .env.example
├─ pyproject.toml
└─ README.md
```

---

```
::contentReference[oaicite:0]{index=0}
```
