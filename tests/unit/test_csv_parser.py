import yaml
from urdu_exec_bot.parsers.signal_csv import SignalCsvParser
from urdu_exec_bot.models.signal import SignalAction


def test_parser_mapping(settings_tmp):
    with open(settings_tmp["settings_path"], "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    p = SignalCsvParser(settings=cfg)
    s = p.parse_line("gc,long")
    assert s is not None
    assert s.instrument == "GC"
    assert s.action == SignalAction.LONG
