# main.py
import time

from utils.config_loader import Config
from utils.logger import log, set_log_file
from utils.cli_parser import parse_cli_args
from utils.time_gate import TimeBasedGate
from utils.schedule_gate import ScheduleGate, FileSessionStorage
from utils.schedule_watcher import ScheduleWatcher
from strategy.entry_policy import EntryPolicy
from signals.reader import SignalReader
from trading.executor import TradeExecutor
from trading.rules import TradeRulesEngine


def parse_and_load_config():
    args = parse_cli_args()
    config = Config()

    if args.mode:
        config.mode = args.mode
        log(f"[CLI] Override mode actif : {config.mode.upper()}", config.logging_enabled)

    if args.log_file:
        config.log_file = args.log_file
        log(f"[CLI] Override log file : {config.log_file}", config.logging_enabled)

    set_log_file(config.log_file)
    return args, config


def _maybe_start_dashboard(config, executor):
    """
    Démarre le dashboard si activé et disponible. Sinon ignore proprement.
    """
    if not getattr(config, "dashboard", {}):
        return
    if not config.dashboard.get("enabled", False):
        return
    try:
        from dashboard.server import start_dashboard  # lazy import
        start_dashboard(config, executor)
        log("[DASHBOARD] Démarré.", config.logging_enabled)
    except Exception as e:
        log(f"[DASHBOARD] Indisponible ({e}). Lancement ignoré.", config.logging_enabled)


def run_monitoring_loop(config, args):
    # Lecteur NDJSON depuis chemin config
    signals_path = config.paths.get("signals_file", "data/input/signals.ndjson")
    signal_reader = SignalReader(signals_path)
    signal_reader.start(reset_pointer=args.reset_pointer)

    # Exécuteur (orchestrateur) + dashboard éventuel
    executor = TradeExecutor(config)
    _maybe_start_dashboard(config, executor)

    # Gate multi-schedules (fenêtres/quotas) + entry policy
    schedules_cfg = config.schedules  # top-level (résolus via ScheduleGate)
    schedule_gate = ScheduleGate(
        schedules_config=schedules_cfg,
        storage=FileSessionStorage(config.paths.get("session_gate_file", "data/state/session_gate.json")),
        logging_enabled=config.logging_enabled,
        strategy_templates=config.strategy_templates
    )
    entry_policy = EntryPolicy(schedule_gate)

    # Règles de décision
    rules_engine = TradeRulesEngine(
        executor,
        inactivity_timeout=5,
        logging_enabled=config.logging_enabled,
        entry_policy=entry_policy
    )

    # Fenêtre globale (peut coexister avec les schedules)
    time_gate = TimeBasedGate(
        start_str=config.trading_hours.get("start_utc", "00:00"),
        stop_str=config.trading_hours.get("stop_utc", "23:59")
    )

    # Watcher pour auto-flatten à la fin d’un schedule si flatten_at_end=true
    schedule_watcher = ScheduleWatcher(config.schedules, logging_enabled=config.logging_enabled)

    log("[URDU BOT] Monitoring actif...", config.logging_enabled)

    try:
        while True:
            # Watcher: détecte fin de schedule et déclenche flatten si requis
            schedule_watcher.tick(executor)

            # Si hors horaires globaux, on ferme si stop_utc et on purge les signaux
            if not time_gate.is_within_trading_hours():
                if time_gate.is_shutdown_time():
                    log("[TIME] ⚠️ Clôture des positions automatique (fin de session).", config.logging_enabled)
                    executor.flatten_all(instrument="*")
                    time.sleep(60)

                # Purge backlog: avance le pointeur de lecture en fin de fichier
                try:
                    if getattr(signal_reader, "_file", None) is not None:
                        signal_reader._file.seek(0, 2)  # EOF
                        signal_reader._position = signal_reader._file.tell()
                except Exception as e:
                    log(f"[SIGNALS] Erreur purge hors horaires: {e}", config.logging_enabled)

                time.sleep(10)
                continue

            # Fenêtre ouverte: consomme les nouveaux signaux
            for signal in signal_reader.read_new_signals():
                log(f"[SIGNAL] Lu depuis NDJSON : {signal}", config.logging_enabled)
                rules_engine.handle_signal(signal)

            rules_engine.tick()
            time.sleep(config.poll_interval_seconds)

    except KeyboardInterrupt:
        log("\n[URDU BOT] Arrêt demandé par l'utilisateur.", config.logging_enabled)
    finally:
        signal_reader.close()
        log("[URDU BOT] Fermeture propre terminée.", config.logging_enabled)


def run_urdu_bot():
    args, config = parse_and_load_config()
    log(f"[URDU BOT] Démarrage en mode : {config.mode.upper()}", config.logging_enabled)

    # Mode probe désactivé ici (garde la boucle principal)
    run_monitoring_loop(config, args)


if __name__ == "__main__":
    run_urdu_bot()
