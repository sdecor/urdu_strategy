---

## ✅ STRUCTURE DU PROJET URDU BOT

```
urdu_bot/
│
├── main.py                          # Point d'entrée principal
├── signals.ndjson                   # Source de signaux (append-only)
├── .env                             # Informations sensibles (clé API, user, etc.)
│
├── config/
│   └── config.yaml                  # Configuration fonctionnelle non sensible
│
├── utils/
│   ├── config_loader.py             # Chargement du YAML + .env
│   ├── logger.py                    # Logger écran + fichier
│   └── cli_parser.py                # Parsing des arguments CLI (--reset-pointer, --mode, etc.)
│
├── signals/
│   └── reader.py                    # Lecture append-only du fichier NDJSON
│
├── trading/
│   ├── executor.py                  # Moteur d'exécution (simulation ou API)
│   ├── simulator.py                 # Simulateur local pour tests
│   └── rules.py                     # Règles métier de la stratégie URDU
│
├── api/
│   └── topstep_client.py           # Wrapper de l'API TopstepX
```

---

## ✅ CONFIGURATION (Exemple `config.yaml`)

```yaml
mode: simulation # ou 'live'
poll_interval_seconds: 1
logging: true
log_file: "urdu_bot.log"

dashboard:
  enabled: true
  host: "127.0.0.1"
  port: 8000

api_endpoints:
  login_key: "/api/Auth/loginKey"
  order_search: "/api/Order/search"
  order_search_open: "/api/Order/searchOpen"
  order_cancel: "/api/Order/cancel"
  position_search_open: "/api/Position/searchOpen"
  contract_available: "/api/Contract/available"
  contract_search: "/api/Contract/search"
  contract_search_by_id: "/api/Contract/searchById"
  order_place: "/api/Order/place"
  account_search: "/api/Account/search"
```

---

## ✅ .env (Exemple)

```dotenv
TOPSTEPX_API_KEY=mon_token
TOPSTEPX_BASE_URL=https://api.topstepx.com
TOPSTEPX_USERNAME=mon_user
TOPSTEPX_ACCOUNT_ID=mon_compte
```

---

## ✅ UTILISATION

### Lancer en simulation (défaut depuis config)

```bash
python main.py
```

### Lancer en simulation et relire tout le fichier

```bash
python main.py --reset-pointer
```

### Lancer en mode live (override config)

```bash
python main.py --mode live
```

### Spécifier un fichier de log personnalisé

```bash
python main.py --log-file logs/test.log
```

---
