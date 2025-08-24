import argparse

def parse_cli_args():
    parser = argparse.ArgumentParser(description="URDU Bot - Trade Automation")

    parser.add_argument(
        "--reset-pointer",
        action="store_true",
        help="Relire le fichier NDJSON depuis le début au démarrage (replay)"
    )

    parser.add_argument(
        "--mode",
        choices=["simulation", "live"],
        help="Override du mode défini dans la configuration"
    )

    parser.add_argument(
        "--log-file",
        help="Override du chemin du fichier de log"
    )

    return parser.parse_args()
