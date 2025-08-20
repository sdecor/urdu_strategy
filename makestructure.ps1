$root = "."

$dirs = @(
  "$root",
  "$root\config",
  "$root\data",
  "$root\data\input",
  "$root\data\archive",
  "$root\logs",
  "$root\state",
  "$root\state\offsets",
  "$root\scripts",
  "$root\src",
  "$root\src\urdu_exec_bot",
  "$root\src\urdu_exec_bot\parsers",
  "$root\src\urdu_exec_bot\models",
  "$root\src\urdu_exec_bot\services",
  "$root\src\urdu_exec_bot\utils",
  "$root\tests",
  "$root\tests\unit",
  "$root\tests\integration",
  "$root\docker"
)

$files = @(
  "$root\pyproject.toml",
  "$root\README.md",
  "$root\.env.example",
  "$root\.gitignore",
  "$root\Makefile",
  "$root\requirements-dev.txt",

  "$root\config\settings.yaml",
  "$root\config\instruments_lots.yaml",
  "$root\config\logging.yaml",
  "$root\config\risk.yaml",

  "$root\data\input\signals.csv",

  "$root\state\trade_state.json",
  "$root\state\offsets\signals.offset",

  "$root\scripts\simulate_signals.py",
  "$root\scripts\backfill_from_csv.py",
  "$root\scripts\reset_state.py",

  "$root\src\urdu_exec_bot\__init__.py",
  "$root\src\urdu_exec_bot\app.py",
  "$root\src\urdu_exec_bot\cli.py",
  "$root\src\urdu_exec_bot\csv_watcher.py",

  "$root\src\urdu_exec_bot\parsers\__init__.py",
  "$root\src\urdu_exec_bot\parsers\signal_csv.py",

  "$root\src\urdu_exec_bot\models\__init__.py",
  "$root\src\urdu_exec_bot\models\signal.py",
  "$root\src\urdu_exec_bot\models\order.py",
  "$root\src\urdu_exec_bot\models\position.py",
  "$root\src\urdu_exec_bot\models\trade_state.py",

  "$root\src\urdu_exec_bot\services\__init__.py",
  "$root\src\urdu_exec_bot\services\strategy_engine.py",
  "$root\src\urdu_exec_bot\services\position_manager.py",
  "$root\src\urdu_exec_bot\services\risk_manager.py",
  "$root\src\urdu_exec_bot\services\pnl_tracker.py",
  "$root\src\urdu_exec_bot\services\lot_sizing.py",
  "$root\src\urdu_exec_bot\services\execution_service.py",
  "$root\src\urdu_exec_bot\services\topstepx_client.py",
  "$root\src\urdu_exec_bot\services\state_store.py",
  "$root\src\urdu_exec_bot\services\event_bus.py",

  "$root\src\urdu_exec_bot\utils\__init__.py",
  "$root\src\urdu_exec_bot\utils\time_utils.py",
  "$root\src\urdu_exec_bot\utils\ids.py",
  "$root\src\urdu_exec_bot\utils\logging_setup.py",

  "$root\tests\conftest.py",
  "$root\tests\unit\test_strategy_engine.py",
  "$root\tests\unit\test_risk_manager.py",
  "$root\tests\unit\test_csv_parser.py",
  "$root\tests\unit\test_execution_service.py",
  "$root\tests\integration\test_topstepx_client.py",
  "$root\tests\integration\test_end_to_end.py",

  "$root\docker\Dockerfile",
  "$root\docker\docker-compose.yml"
)

$dirs  | ForEach-Object { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
$files | ForEach-Object { if (-not (Test-Path $_)) { New-Item -ItemType File -Path $_ -Force | Out-Null } }
