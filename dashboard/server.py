import threading
from datetime import datetime
from flask import Flask, jsonify, Response
from utils.logger import log
from utils.state import STATE


def _tail_log(path: str, max_lines: int = 200) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [ln.rstrip("\n") for ln in lines[-max_lines:]]
    except Exception:
        return []


def create_app(config, executor):
    app = Flask(__name__)

    @app.get("/")
    def index():
        html = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"/>
<title>URDU bot — Dashboard</title><meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
:root{{--bg:#0f1220;--card:#171a2b;--text:#e8eaf6;--muted:#9aa0b7;--accent:#7aa2f7}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial}}
header{{padding:16px 20px;background:linear-gradient(90deg,#1b1e34,#171a2b);position:sticky;top:0;border-bottom:1px solid #20243a}}
h1{{margin:0;font-size:18px;letter-spacing:.5px}}
.grid{{display:grid;gap:16px;padding:16px;grid-template-columns: repeat(auto-fit,minmax(320px,1fr))}}
.card{{background:var(--card);border:1px solid #22253a;border-radius:12px;padding:14px;box-shadow:0 4px 16px rgb(0 0 0 /.2)}}
.kpis{{display:flex;gap:12px;flex-wrap:wrap}}
.kpi{{background:#121428;border:1px solid #232746;padding:12px 14px;border-radius:10px;min-width:120px}}
.kpi b{{display:block;font-size:12px;color:var(--muted);margin-bottom:6px}}
.kpi span{{font-size:18px}}
.pill{{padding:2px 8px;border-radius:999px;font-size:12px;border:1px solid #2a2f52}}
.pill.live{{background:#111c2b;color:#9bcaff;border-color:#1b3358}}
.list{{display:flex;flex-direction:column;gap:8px;max-height:360px;overflow:auto}}
.row{{display:flex;gap:10px;justify-content:space-between;align-items:center;background:#121428;border:1px solid #232746;padding:10px;border-radius:8px}}
.mono{{font-family:ui-monospace,Consolas,Menlo,Monaco,monospace;font-size:12px;color:#d2d6f1}}
.muted{{color:#9aa0b7}}
.section-title{{margin:0 0 10px;font-size:14px;color:#c6cbf5}}
.btn{{display:inline-block;background:#1c2344;color:#cfe0ff;border:1px solid #2b3a76;padding:8px 12px;border-radius:8px;text-decoration:none;cursor:pointer}}
.btn:hover{{background:#212a54}}
footer{{padding:8px 16px;color:#7c84a9;font-size:12px;border-top:1px solid #22253a}}
</style></head>
<body>
<header><h1>URDU bot — Dashboard <span class="pill live">{config.mode.upper()}</span> <span class="pill">port {config.dashboard.get("port", 5001)}</span></h1></header>
<div class="grid">
  <div class="card">
    <div class="kpis">
      <div class="kpi"><b>Position</b><span id="kpi-pos">—</span></div>
      <div class="kpi"><b>Contrat</b><span class="mono">{config.contract_id or "—"}</span></div>
      <div class="kpi"><b>Compte</b><span class="mono">{config.account_id or "—"}</span></div>
      <div class="kpi"><b>Lots (def.)</b><span class="mono">{getattr(config, "default_quantity", 1)}</span></div>
      <div class="kpi"><b>Log file</b><span class="mono">{config.log_file}</span></div>
    </div>
  </div>
  <div class="card"><h3 class="section-title">Signaux récents</h3><div id="signals" class="list"></div></div>
  <div class="card"><h3 class="section-title">Actions (règles)</h3><div id="actions" class="list"></div></div>
  <div class="card"><h3 class="section-title">Trades (exécutions)</h3><div id="trades" class="list"></div></div>
  <div class="card"><h3 class="section-title">Positions & ordres (live)</h3><div class="list" id="live"></div></div>
  <div class="card"><h3 class="section-title">Log (fin du fichier)</h3><div id="logtail" class="list"></div></div>
</div>
<footer>Dernière MAJ: <span id="now"></span> <a class="btn" onclick="refresh()">Rafraîchir</a></footer>
<script>
async function refresh(){{
  const res = await fetch("/api/snapshot");
  const data = await res.json();
  document.getElementById("kpi-pos").textContent = data.state.current_position;

  const renderList = (elId, arr, fn) => {{
    const el = document.getElementById(elId);
    el.innerHTML = "";
    (arr || []).forEach(item => {{
      const row = document.createElement("div");
      row.className = "row mono";
      row.innerHTML = fn(item);
      el.appendChild(row);
    }});
  }};

  renderList("signals", data.state.signals, (it)=>`<span class="muted">${{it.ts}}</span><span>${{JSON.stringify(it.signal)}}</span>`);
  renderList("actions", data.state.actions, (it)=>`<span class="muted">${{it.ts}}</span><span>${{it.action}} <b>${{it.instrument}}</b></span>`);
  renderList("trades", data.state.trades, (it)=>`<span class="muted">${{it.ts}}</span><span>pos=${{it.position}} qty=${{it.quantity}} <b>${{it.instrument}}</b></span><span>${{it.result ? JSON.stringify(it.result) : ""}}</span>`);

  const liveEl = document.getElementById("live");
  liveEl.innerHTML = "";
  if (data.live) {{
    const pos = document.createElement("div");
    pos.className = "row mono";
    pos.innerHTML = `<b>open positions</b> <span>${{JSON.stringify(data.live.open_positions)}}</span>`;
    liveEl.appendChild(pos);

    const ord = document.createElement("div");
    ord.className = "row mono";
    ord.innerHTML = `<b>working orders</b> <span>${{JSON.stringify(data.live.working_orders)}}</span>`;
    liveEl.appendChild(ord);
  }} else {{
    const info = document.createElement("div");
    info.className = "row mono";
    info.textContent = "— mode simulation ou données live indisponibles —";
    liveEl.appendChild(info);
  }}

  document.getElementById("logtail").innerHTML = (data.log_tail || []).map(l=>`<div class="row mono">${{l}}</div>`).join("");
  document.getElementById("now").textContent = new Date().toLocaleString();
}}
refresh(); setInterval(refresh, 2000);
</script>
</body></html>"""
        return Response(html, mimetype="text/html")

    @app.get("/api/snapshot")
    def api_snapshot():
        state = STATE.snapshot()
        log_tail = _tail_log(config.log_file, max_lines=200)

        live = None
        try:
            if config.mode == "live" and hasattr(executor, "engine"):
                eng = executor.engine
                get_pos = getattr(eng, "get_open_positions", None)
                get_ord = getattr(eng, "get_working_orders", None)
                if callable(get_pos) and callable(get_ord):
                    live = {
                        "open_positions": get_pos(),
                        "working_orders": get_ord()
                    }
        except Exception as e:
            log(f"[DASH] Erreur récupération live: {e}", config.logging_enabled)

        payload = {
            "now": datetime.utcnow().isoformat() + "Z",
            "mode": config.mode,
            "state": state,
            "log_tail": log_tail,
            "live": live
        }
        return jsonify(payload)

    return app


def start_dashboard(config, executor):
    if not config.dashboard.get("enabled", True):
        return

    host = config.dashboard.get("host", "127.0.0.1")
    port = int(config.dashboard.get("port", 5001))
    app = create_app(config, executor)

    def _run():
        log(f"[DASH] Démarrage dashboard sur http://{host}:{port}", config.logging_enabled)
        app.run(host=host, port=port, debug=False, use_reloader=False)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
