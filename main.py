import time
from utils.config_loader import Config
from utils.logger import log, set_log_file
from utils.cli_parser import parse_cli_args
from signals.reader import SignalReader
from trading.executor import TradeExecutor
from trading.rules import TradeRulesEngine


def main():
    # 🧩 CLI args
    args = parse_cli_args()

    # ⚙️ Config
    config = Config()

    # Override du mode
    if args.mode:
        config.mode = args.mode
        log(f"[CLI] Override mode actif : {config.mode.upper()}", config.logging_enabled)

    # Override fichier de log
    if args.log_file:
        config.log_file = args.log_file
        log(f"[CLI] Override log file : {config.log_file}", config.logging_enabled)

    # Appliquer le fichier log
    set_log_file(config.log_file)

    log(f"[URDU BOT] Démarrage en mode : {config.mode.upper()}", config.logging_enabled)

    # SignalReader
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


if __name__ == "__main__":
    main()
