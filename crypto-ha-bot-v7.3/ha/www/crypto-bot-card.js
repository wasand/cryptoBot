class CryptoBotCard extends HTMLElement {
  setConfig(config) {
    if (!config.backend_url) throw new Error("Set backend_url in card config");
    this.config = config;
    this.attachShadow({ mode: "open" });
    this.render();
    this.refresh();
    this.timer = setInterval(() => this.refresh(), 30000);
  }
  disconnectedCallback(){ if (this.timer) clearInterval(this.timer); }

  async refresh() {
    const b = this.config.backend_url;
    const pairs = this.config.pairs || ["BTCUSDC","ETHUSDC"];
    try {
      const [health, conf, logs, alerts, p1, p2] = await Promise.all([
        fetch(`${b}/health`).then(r=>r.json()),
        fetch(`${b}/config`).then(r=>r.json()),
        fetch(`${b}/logs?limit=50`).then(r=>r.json()),
        fetch(`${b}/alerts?limit=50`).then(r=>r.json()),
        fetch(`${b}/market/history?pair=${pairs[0]}&limit=100`).then(r=>r.json()),
        fetch(`${b}/market/history?pair=${pairs[1]}&limit=100`).then(r=>r.json()),
      ]);
      this.state = { health, conf, logs, alerts, h1: p1.points||[], h2: p2.points||[], pairs };
    } catch (e) {
      this.state = { error: e.toString() };
    }
    this.render();
  }

  async post(url, body) {
    const res = await fetch(url, { method: "POST", headers: {"Content-Type":"application/json"}, body: body ? JSON.stringify(body) : null });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
  async put(url, body) {
    const res = await fetch(url, { method: "PUT", headers: {"Content-Type":"application/json"}, body: JSON.stringify(body||{}) });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async onStart(){ await this.post(`${this.config.backend_url}/start`, { pairs: this.state.pairs, autotrade: this.shadowRoot.getElementById("autotrade").checked }); this.refresh(); }
  async onStop(){ await this.post(`${this.config.backend_url}/stop`); this.refresh(); }
  async onBuy(){
    const pair = this.shadowRoot.getElementById("pair").value || this.state.pairs[0];
    const amt = parseFloat(this.shadowRoot.getElementById("amt").value || "50");
    await this.post(`${this.config.backend_url}/order/buy`, { pair, quote_amount_usd: amt }); this.refresh();
  }
  async onSell(){
    const pair = this.shadowRoot.getElementById("pair").value || this.state.pairs[0];
    await this.post(`${this.config.backend_url}/order/sell`, { pair }); this.refresh();
  }
  async onSaveConfig(){
    const body = {
      min_profit_pct: parseFloat(this.shadowRoot.getElementById("min_profit").value),
      hysteresis_pct: parseFloat(this.shadowRoot.getElementById("hyst").value),
      buy_drawdown_pct: parseFloat(this.shadowRoot.getElementById("dd").value),
      min_trades_per_hour: parseInt(this.shadowRoot.getElementById("tph").value),
      base_package_usd: parseFloat(this.shadowRoot.getElementById("baseusd").value),
      downtrend_multiplier: parseFloat(this.shadowRoot.getElementById("mult").value),
      buy_lookback: this.shadowRoot.getElementById("lookback").value,
    };
    await this.put(`${this.config.backend_url}/config`, body);
    this.refresh();
  }
  async onClearAlerts(){
    await fetch(`${this.config.backend_url}/alerts`, { method: "DELETE" });
    this.refresh();
  }

  render(){
    const st = this.state || {};
    const h = (arr)=>arr && arr.length ? this.sparkline(arr.map(p=>parseFloat(p.price))) : "";
    const c = st.conf || {};
    const style = `
      <style>
        .card{padding:16px;font-family: var(--primary-font-family, Roboto, Arial);}
        .row{display:flex;gap:12px;flex-wrap:wrap;}
        .box{flex:1 1 320px;border:1px solid var(--divider-color, #ddd);border-radius:12px;padding:12px;}
        .btn{padding:8px 12px;border-radius:8px;border:0;background: var(--primary-color, #03a9f4);color:white;cursor:pointer;margin-right:8px;}
        .btn.warn{background:#f44336;}
        .btn.secondary{background:#607d8b;}
        table{width:100%;border-collapse: collapse;font-size: 12px;}
        th, td{padding:6px;border-bottom:1px solid #eee;text-align:left;}
        input, select{padding:6px 8px;border:1px solid #ccc;border-radius:8px;margin-right:8px;}
        .spark{width:100%;height:60px;display:block;}
        .title{font-weight:600;margin-bottom:6px;}
        label{font-size:12px;margin-right:6px;}
      </style>`;

    const controls = `
      <div class="box">
        <div class="title">Sterowanie</div>
        <label><input type="checkbox" id="autotrade" ${st.health && st.health.autotrade ? "checked":""}> Autotrade</label><br/><br/>
        <button class="btn" id="start">Start</button>
        <button class="btn warn" id="stop">Stop</button>
        <div style="margin-top:8px;">
          <input id="pair" placeholder="Para (BTCUSDC)" value="${(st.pairs||["BTCUSDC"])[0]}">
          <input id="amt" type="number" step="1" min="5" value="${c.base_package_usd||50}">
          <button class="btn secondary" id="buy">Kup pakiet</button>
          <button class="btn secondary" id="sell">Sprzedaj</button>
          <button class="btn" id="clear">Wyczyść alerty</button>
        </div>
        <div style="margin-top:8px;font-size:12px;">Status: ${st.health? (st.health.running?"RUNNING":"STOPPED") : "-"} | Pary: ${(st.health && st.health.pairs)? st.health.pairs.join(", ") : ""}</div>
      </div>`;

    const charts = `
      <div class="box">
        <div class="title">${(st.pairs||["BTCUSDC","ETHUSDC"])[0]} – ostatnie ceny</div>
        <svg class="spark" viewBox="0 0 100 30">${h(st.h1)}</svg>
        <div class="title" style="margin-top:8px;">${(st.pairs||["BTCUSDC","ETHUSDC"])[1]} – ostatnie ceny</div>
        <svg class="spark" viewBox="0 0 100 30">${h(st.h2)}</svg>
      </div>`;

    const configBox = `
      <div class="box">
        <div class="title">Konfiguracja strategii</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;">
          <label>Min profit % <input id="min_profit" type="number" step="0.1" value="${c.min_profit_pct||5}"></label>
          <label>Histereza % <input id="hyst" type="number" step="0.1" value="${c.hysteresis_pct||1}"></label>
          <label>Drawdown (kupno) % <input id="dd" type="number" step="0.1" value="${c.buy_drawdown_pct||3}"></label>
          <label>Min transakcji/h <input id="tph" type="number" step="1" value="${c.min_trades_per_hour||100}"></label>
          <label>Pakiet USD <input id="baseusd" type="number" step="1" value="${c.base_package_usd||50}"></label>
          <label>Mult. downtrend <input id="mult" type="number" step="0.1" value="${c.downtrend_multiplier||2}"></label>
          <label>Lookback
            <select id="lookback">
              <option value="day" ${c.buy_lookback==="day"?"selected":""}>Day</option>
              <option value="week" ${c.buy_lookback==="week"?"selected":""}>Week</option>
              <option value="month" ${c.buy_lookback==="month"?"selected":""}>Month</option>
            </select>
          </label>
          <button class="btn" id="savecfg">Zapisz</button>
        </div>
      </div>`;

    const logs = `
      <div class="box">
        <div class="title">Ostatnie logi</div>
        <table><thead><tr><th>czas</th><th>para</th><th>lvl</th><th>komunikat</th><th>pnl $</th><th>pnl %</th></tr></thead>
        <tbody>
          ${(st.logs||[]).map(r=>`<tr><td>${r.ts||""}</td><td>${r.pair||""}</td><td>${r.level||""}</td><td>${r.message||""}</td><td>${r.pnl_usd??""}</td><td>${r.pnl_percent??""}</td></tr>`).join("")}
        </tbody></table>
      </div>`;

    const alerts = `
      <div class="box">
        <div class="title">Alerty</div>
        <table><thead><tr><th>czas</th><th>para</th><th>typ</th><th>pnl $</th><th>pnl %</th></tr></thead>
        <tbody>
          ${(st.alerts||[]).map(a=>`<tr><td>${a.ts||""}</td><td>${a.pair||""}</td><td>${a.type||""}</td><td>${a.pnl_usd??""}</td><td>${a.pnl_percent??""}</td></tr>`).join("")}
        </tbody></table>
      </div>`;

    const html = `
      <div class="card">
        <div class="row">${controls}${charts}</div>
        <div class="row">${configBox}</div>
        <div class="row">${logs}${alerts}</div>
      </div>`;

    this.shadowRoot.innerHTML = style + html;
    const $ = (id)=>this.shadowRoot.getElementById(id);
    if ($("start")) $("start").onclick = ()=>this.onStart();
    if ($("stop")) $("stop").onclick = ()=>this.onStop();
    if ($("buy")) $("buy").onclick = ()=>this.onBuy();
    if ($("sell")) $("sell").onclick = ()=>this.onSell();
    if ($("savecfg")) $("savecfg").onclick = ()=>this.onSaveConfig();
    if ($("clear")) $("clear").onclick = ()=>this.onClearAlerts();
  }

  sparkline(values){
    if (!values || values.length<2) return "";
    const min = Math.min(...values), max = Math.max(...values);
    const scale = v => (max===min)?15: ( (v - min) / (max - min) * 28 + 1 );
    const step = 100/(values.length-1);
    let d = "";
    values.forEach((v,i)=>{
      const x = i*step, y = 30 - scale(v);
      d += (i===0?`M ${x} ${y}`:` L ${x} ${y}`);
    });
    return `<path d="${d}" stroke="currentColor" stroke-width="1" fill="none"></path>`;
  }
  getCardSize(){ return 8; }
}
customElements.define("crypto-bot-card", CryptoBotCard);
