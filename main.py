import time
from utils.config_loader import Config
from utils.logger import log, set_log_file
from utils.cli_parser import parse_cli_args
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
    signal_reader = SignalReader("signals.ndjson")
    signal_reader.start(reset_pointer=args.reset_pointer)

    executor = TradeExecutor(config)
    rules_engine = TradeRulesEngine(executor, inactivity_timeout=5, logging_enabled=config.logging_enabled)

    log("[URDU BOT] Monitoring actif...", config.logging_enabled)

    try:
        while True:
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
