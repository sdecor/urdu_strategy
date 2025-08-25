import time
from datetime import time as dtime

from utils.config_loader import Config
from utils.logger import log, set_log_file
from utils.cli_parser import parse_cli_args
from utils.time_gate import TimeBasedGate
from signals.reader import SignalReader
from trading.executor import TradeExecutor
from trading.rules import TradeRulesEngine
from dashboard.server import start_dashboard


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


def run_probe_sequence(config):
    if config.mode != "live":
        log("[PROBE] Le test manuel API nécessite --mode live.", config.logging_enabled)
        return

    executor = TradeExecutor(config)
    start_dashboard(config, executor)
    rules_engine = TradeRulesEngine(executor, inactivity_timeout=5, logging_enabled=config.logging_enabled)
    client = executor.engine

    qty = config.default_quantity
    log(f"[PROBE] 1/3 Ouverture d'un ordre MARKET size={qty}", config.logging_enabled)
    client.execute_trade(instrument="N/A", position=1, size=qty)

    log("[PROBE] 2/3 Récupération des positions ouvertes", config.logging_enabled)
    positions = client.get_open_positions()
    log(f"[PROBE] Positions ouvertes (brut): {positions}", config.logging_enabled)

    log("[PROBE] 3/3 Flatten all", config.logging_enabled)
    client.flatten_all()

    log("[PROBE] Séquence complète terminée.", config.logging_enabled)


def run_monitoring_loop(config, args):
    # Chemin des signaux via la config (ex: paths.signals_file: "data/input/signals.ndjson")
    signal_reader = SignalReader(config.paths["signals_file"])
    signal_reader.start(reset_pointer=args.reset_pointer)

    executor = TradeExecutor(config)
    rules_engine = TradeRulesEngine(executor, inactivity_timeout=5, logging_enabled=config.logging_enabled)

    # Fenêtre horaire depuis la config (trading_hours.start_utc / stop_utc)
    time_gate = TimeBasedGate(
        start_str=config.trading_hours.get("start_utc", "02:00"),
        stop_str=config.trading_hours.get("stop_utc", "20:05")
    )

    log("[URDU BOT] Monitoring actif...", config.logging_enabled)

    try:
        while True:
            # Hors horaires : on PURGE le backlog en plaçant le pointeur en fin de fichier
            # => À 02:00 UTC, seuls les nouveaux signaux seront pris en compte
            if not time_gate.is_within_trading_hours():
                if time_gate.is_shutdown_time():
                    log("[TIME] ⚠️ Clôture des positions automatique (fin de session).", config.logging_enabled)
                    executor.engine.flatten_all()
                    # Attendre un peu pour éviter les répétitions de fermeture
                    time.sleep(60)

                # Purge des signaux hors horaires : avancer le pointeur à la fin
                try:
                    if getattr(signal_reader, "_file", None) is not None:
                        signal_reader._file.seek(0, 2)  # EOF
                        signal_reader._position = signal_reader._file.tell()
                except Exception as e:
                    log(f"[SIGNALS] Erreur purge hors horaires: {e}", config.logging_enabled)

                time.sleep(10)
                continue

            # Fenêtre de trading ouverte : traiter les nouveaux signaux
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

    if args.probe_api:
        run_probe_sequence(config)
    else:
        run_monitoring_loop(config, args)


if __name__ == "__main__":
    run_urdu_bot()
