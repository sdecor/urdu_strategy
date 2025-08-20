README.md

````md
# URDU Exec Bot

Service qui lit un CSV de signaux (instrument, action) et exécute des ordres via l’API TopstepX.  
Stratégie « URDU » : à chaque `EXIT`, on **inverse** (long→short, short→long).  
Risque : **flat toutes positions** si PnL jour ≥ seuil défini (par défaut 2000 USD).

---

## 1) Prérequis

- Python 3.11+
- PowerShell (Windows)
- Accès à une clé API TopstepX (compte et endpoints valides)
- Git (optionnel)
- Docker & Docker Compose (optionnel)

---

## 2) Installation (local)

```powershell
# Cloner ou copier le projet, puis :
cd .\URDU_bot

# (Optionnel) Environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Dépendances
pip install -r requirements-dev.txt
```
````

---

## 3) Configuration

### 3.1 Variables d’environnement

Copier le gabarit et renseigner vos valeurs :

```powershell
Copy-Item .env.example .env
notepad .env
```

`.env` :

```env
TOPSTEPX_API_KEY=VOTRE_CLE_API
SETTINGS_PATH=./config/settings.yaml
```

### 3.2 Fichiers YAML

- `config/settings.yaml` : chemins, polling, mapping CSV, endpoints TopstepX, etc.
- `config/instruments_lots.yaml` : lots fixes par instrument.
- `config/risk.yaml` : seuil PnL jour.
- `config/logging.yaml` : logs.

Valeurs par défaut (extrait) :

```yaml
paths:
  csv_input: data/input/signals.csv
config_files:
  lots: config/instruments_lots.yaml
  risk: config/risk.yaml
  logging: config/logging.yaml
polling:
  interval_ms: 500
csv_reader:
  delimiter: ","
  schema: ["instrument", "action"]
  action_mapping:
    long: LONG
    buy: LONG
    short: SHORT
    sell: SHORT
    exit: EXIT
topstepx:
  base_url: https://api.topstepx.com
  account_id: REPLACE_ME
  auth:
    api_key_env: TOPSTEPX_API_KEY
```

---

## 4) Format du CSV de signaux

Chemin par défaut : `data/input/signals.csv` (append-only).
Schéma : `instrument,action`

Exemples valides :

```
GC,long
UB,short
ES,exit
```

Actions acceptées (case-insensitive) : `long|buy`, `short|sell`, `exit`.

---

## 5) Lancer le service (local)

```powershell
# Variables d’environnement pour la session si besoin
$env:TOPSTEPX_API_KEY = "<VOTRE_CLE>"
$env:SETTINGS_PATH = ".\config\settings.yaml"

# Démarrage
python -u .\src\urdu_exec_bot\app.py
```

Le service :

- lit les nouvelles lignes de `signals.csv`,
- calcule les ordres à envoyer,
- exécute via TopstepX,
- applique le risque (flat all si PnL jour ≥ seuil),
- persiste l’état dans `state/`.

---

## 6) Générer des signaux (outils)

### 6.1 Simulation simple

```powershell
python .\scripts\simulate_signals.py -i GC -a long
python .\scripts\simulate_signals.py -i GC -a exit
python .\scripts\simulate_signals.py -i UB -a short -c 3 -t 200
```

### 6.2 Rejouer un fichier d’historique

```powershell
python .\scripts\backfill_from_csv.py -s .\mes_signaux.csv -t 100 -n 1000 -k 10
```

### 6.3 RAZ de l’état / archivage des signaux

```powershell
# Archive le CSV courant et remet l’état à zéro
python .\scripts\reset_state.py --archive-signals

# Ou simplement vider le CSV et reset l’état
python .\scripts\reset_state.py --clear-signals
```

---

## 7) Docker / Docker Compose

```powershell
Copy-Item .env.example .env
notepad .env   # renseigner TOPSTEPX_API_KEY

docker compose up --build -d
docker compose logs -f
```

Le service lit/écrit via les volumes mappés (`config/`, `data/`, `logs/`, `state/`).

---

## 8) Tests

```powershell
pytest -q
```

---

## 9) Arborescence

```
.
├─ config/
├─ data/
│  └─ input/signals.csv
├─ logs/
├─ scripts/
├─ src/
│  └─ urdu_exec_bot/
├─ state/
│  └─ offsets/
├─ tests/
└─ docker/
```

---

## 10) Commandes utiles (rappel)

### Lancer l’app

```powershell
python -u .\src\urdu_exec_bot\app.py
```

### Envoyer un signal rapide

```powershell
python .\scripts\simulate_signals.py -i GC -a long
```

### RAZ + archive

```powershell
python .\scripts\reset_state.py --archive-signals
```

---

## 11) Dépannage rapide

- **Erreur d’auth TopstepX** : vérifier `TOPSTEPX_API_KEY` et `topstepx.account_id`.
- **Pas d’ordres envoyés** : vérifier que `signals.csv` s’incrémente et que le mapping `action_mapping` couvre vos valeurs.
- **Rien ne se passe** : ajuster `polling.interval_ms` (ex. 200 ms) et regarder `logs/app.log`.
- **Seuil de risque** : `config/risk.yaml` → `pnl.daily_close_all_when_gte`.

---

```

```
