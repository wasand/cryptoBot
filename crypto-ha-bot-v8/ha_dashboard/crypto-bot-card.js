class CryptoBotCard extends HTMLElement {
  setConfig(config) {
    if (!config.backend_url) throw new Error("Set backend_url in card config");
    this.config = config;
    this.attachShadow({ mode: "open" });
    this.render();
    this.refresh();
    this.timer = setInterval(() => this.refresh(), 30000);
  }
  disconnectedCallback() { if (this.timer) clearInterval(this.timer); }

  async refresh() {
    const b = this.config.backend_url;
    const pairs = this.config.pairs || ["BTCUSDC", "ETHUSDC"];
    try {
      const [health, conf, logs, alerts, p1, p2] = await Promise.all([
        fetch(`${b}/health`).then(r => r.json()),
        fetch(`${b}/config`).then(r => r.json()),
        fetch(`${b}/logs?limit=50`).then(r => r.json()),
        fetch(`${b}/alerts?limit=50`).then(r => r.json()),
        fetch(`${b}/market/history?pair=${pairs[0]}&limit=100`).then(r => r.json()),
        fetch(`${b}/market/history?pair=${pairs[1]}&limit=100`).then(r => r.json()),
      ]);
      this.state = { health, conf, logs, alerts, h1: p1.points || [], h2: p2.points || [], pairs };
    } catch (e) {
      this.state = { error: e.toString() };
    }
    this.render();
  }

  async post(url, body) {
    const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : null });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
  async put(url, body) {
    const res = await fetch(url, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async onStart() { await this.post(`${this.config.backend_url}/start`, { pairs: this.state.pairs, autotrade: this.shadowRoot.getElementById("autotrade").checked }); this.refresh(); }
  async onStop() { await this.post(`${this.config.backend_url}/stop`); this.refresh(); }
  async onBuy() {
    const pair = this.shadowRoot.getElementById("pair").value || this.state.pairs[0];
    const amt = parseFloat(this.shadowRoot.getElementById("amount").value) || 50;
    await this.post(`${this.config.backend_url}/order/buy`, { pair, quote_amount_usd: amt });
    this.refresh();
  }
  async onSell() {
    const pair = this.shadowRoot.getElementById("pair").value || this.state.pairs[0];
    await this.post(`${this.config.backend_url}/order/sell`, { pair });
    this.refresh();
  }
  async onSaveConfig() {
    const cfg = {
      min_profit_pct: parseFloat(this.shadowRoot.getElementById("min_profit").value),
      hysteresis_pct: parseFloat(this.shadowRoot.getElementById("hysteresis").value),
      buy_drawdown_pct: parseFloat(this.shadowRoot.getElementById("drawdown").value),
      min_trades_per_hour: parseInt(this.shadowRoot.getElementById("min_trades").value),
      base_package_usd: parseFloat(this.shadowRoot.getElementById("base_package").value),
      downtrend_multiplier: parseFloat(this.shadowRoot.getElementById("multiplier").value),
      buy_lookback: this.shadowRoot.getElementById("lookback").value
    };
    await this.put(`${this.config.backend_url}/config`, cfg);
    this.refresh();
  }
  async onClearAlerts() {
    await this.post(`${this.config.backend_url}/alerts`, null);
    this.refresh();
  }

  render() {
    const st = this.state || {};
    const style = `
      <style>
        .card { padding: 16px; font-family: Arial; }
        .row { display: flex; gap: 16px; margin-bottom: 16px; }
        .box { border: 1px solid #ccc; padding: 8px; flex: 1; }
        .title { font-weight: bold; margin-bottom: 8px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ccc; padding: 4px; }
        input, select, button { margin: 4px; }
        svg { width: 100px; height: 30px; }
      </style>`;

    const controls = `
      <div class="box">
        <div class="title">Sterowanie</div>
        <div>Status: ${st.health?.running ? "Działa" : "Zatrzymany"}</div>
        <div>Autotrade: <input type="checkbox" id="autotrade" ${st.health?.autotrade ? "checked" : ""}></div>
        <button id="start">Start</button>
        <button id="stop">Stop</button>
        <div>
          Para: <select id="pair">${(st.pairs || []).map(p => `<option value="${p}">${p}</option>`).join("")}</select>
          Kwota USD: <input type="number" id="amount" value="50">
          <button id="buy">Kup</button>
          <button id="sell">Sprzedaj</button>
        </div>
      </div>`;

    const charts = `
      <div class="box">
        <div class="title">Wykresy</div>
        <div>Pair 1 (${st.pairs?.[0] || ""}): <svg viewBox="0 0 100 30">${this.sparkline(st.h1?.map(p => p.price))}</svg></div>
        <div>Pair 2 (${st.pairs?.[1] || ""}): <svg viewBox="0 0 100 30">${this.sparkline(st.h2?.map(p => p.price))}</svg></div>
      </div>`;

    const configBox = `
      <div class="box">
        <div class="title">Konfiguracja strategii</div>
        <div>Min zysk %: <input type="number" id="min_profit" value="${st.conf?.min_profit_pct || 5}"></div>
        <div>Histereza %: <input type="number" id="hysteresis" value="${st.conf?.hysteresis_pct || 1}"></div>
        <div>Drawdown %: <input type="number" id="drawdown" value="${st.conf?.buy_drawdown_pct || 3}"></div>
        <div>Min transakcji/h: <input type="number" id="min_trades" value="${st.conf?.min_trades_per_hour || 100}"></div>
        <div>Pakiet bazowy USD: <input type="number" id="base_package" value="${st.conf?.base_package_usd || 50}"></div>
        <div>Mnożnik downtrend: <input type="number" id="multiplier" value="${st.conf?.downtrend_multiplier || 2}"></div>
        <div>Lookback: <select id="lookback">
          <option value="day" ${st.conf?.buy_lookback === "day" ? "selected" : ""}>Dzień</option>
          <option value="week" ${st.conf?.buy_lookback === "week" ? "selected" : ""}>Tydzień</option>
          <option value="month" ${st.conf?.buy_lookback === "month" ? "selected" : ""}>Miesiąc</option>
        </select></div>
        <button id="savecfg">Zapisz</button>
      </div>`;

    const logs = `
      <div class="box">
        <div class="title">Logi</div>
        <table><thead><tr><th>czas</th><th>para</th><th>lvl</th><th>komunikat</th><th>pnl $</th><th>pnl %</th></tr></thead>
        <tbody>
          ${(st.logs || []).map(r => `<tr><td>${r.ts || ""}</td><td>${r.pair || ""}</td><td>${r.level || ""}</td><td>${r.message || ""}</td><td>${r.pnl_usd ?? ""}</td><td>${r.pnl_percent ?? ""}</td></tr>`).join("")}
        </tbody></table>
      </div>`;

    const alerts = `
      <div class="box">
        <div class="title">Alerty</div>
        <button id="clear">Wyczyść alerty</button>
        <table><thead><tr><th>czas</th><th>para</th><th>typ</th><th>pnl $</th><th>pnl %</th></tr></thead>
        <tbody>
          ${(st.alerts || []).map(a => `<tr><td>${a.ts || ""}</td><td>${a.pair || ""}</td><td>${a.type || ""}</td><td>${a.pnl_usd ?? ""}</td><td>${a.pnl_percent ?? ""}</td></tr>`).join("")}
        </tbody></table>
      </div>`;

    const html = `
      <div class="card">
        <div class="row">${controls}${charts}</div>
        <div class="row">${configBox}</div>
        <div class="row">${logs}${alerts}</div>
      </div>`;

    this.shadowRoot.innerHTML = style + html;
    const $ = (id) => this.shadowRoot.getElementById(id);
    if ($("start")) $("start").onclick = () => this.onStart();
    if ($("stop")) $("stop").onclick = () => this.onStop();
    if ($("buy")) $("buy").onclick = () => this.onBuy();
    if ($("sell")) $("sell").onclick = () => this.onSell();
    if ($("savecfg")) $("savecfg").onclick = () => this.onSaveConfig();
    if ($("clear")) $("clear").onclick = () => this.onClearAlerts();
  }

  sparkline(values) {
    if (!values || values.length < 2) return "";
    const min = Math.min(...values), max = Math.max(...values);
    const scale = v => (max === min) ? 15 : ((v - min) / (max - min) * 28 + 1);
    const step = 100 / (values.length - 1);
    let d = "";
    values.forEach((v, i) => {
      const x = i * step, y = 30 - scale(v);
      d += (i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`);
    });
    return `<path d="${d}" stroke="currentColor" stroke-width="1" fill="none"></path>`;
  }
  getCardSize() { return 8; }
}
customElements.define("crypto-bot-card", CryptoBotCard);