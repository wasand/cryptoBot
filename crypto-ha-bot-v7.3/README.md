# Crypto HA Bot v7.3 – komplet testnet (Docker + MariaDB + Home Assistant custom card)

Wersja zawiera:
- **Autotrade** (kupno/sprzedaż pakietów) wg parametrów: min profit %, histereza %, drawdown %, min transakcji/h, mnożnik w downtrendzie, lookback (day/week/month).
- **Pakiety**: każdy zakup to osobny pakiet; sprzedaż per‑pakiet; realizowane PnL w USD (PLN możliwy po dodaniu FX).
- **Kolektor 5m** dla par (domyślnie BTCUSDC, ETHUSDC) + EMA (szybka/wolna), TPH (transakcje/h).
- **Alerty PnL** z progami dodatnim/ujemnym.
- **Konfiguracja par** (allowed + risk 0..10) – przez API `/pair-config`.
- **Kursy FX (USD→PLN/EUR/GBP/CHF)** co godzinę (opcjonalne; `FX_ENABLED=true`).
- **Akcje „wielkiej trójki”** – placeholder co godzinę (`EQUITIES_ENABLED=false` domyślnie).
- **Custom card** do HA: start/stop, autotrade, kup/sprzedaj, zapis konfiguracji strategii, dwa mini‑wykresy, logi, alerty, „Wyczyść alerty”.
- **Logi/alerty/market data** w MariaDB.
- **Check connection**: `python -m app.check_connection`.

## Uruchomienie
1. **Baza**: w MariaDB utwórz bazę `crypto_bot` i użytkownika `crypto_bot` (host: `core-mariadb` jeśli używasz dodatku HA).
2. **.env**: skopiuj `.env.example` → `.env` i uzupełnij (klucze Binance *testnet*, DB, pary itd.).
3. **Docker**:
```bash
docker compose up -d --build
docker compose exec trading-bot python -m app.check_connection
# opcjonalnie: zasiej przykładowe dane, aby wykresy działały od razu
docker compose exec trading-bot python -m app.seed_example
```
4. **Home Assistant – custom card**:
   - Skopiuj `ha/www/crypto-bot-card.js` → `/config/www/crypto-bot-card.js`.
   - Ustawienia → Panele → Zasoby → **Dodaj zasób**:
     - URL: `/local/crypto-bot-card.js`
     - Typ: **JavaScript Module**
   - Dodaj kartę *Manual*:
```yaml
type: custom:crypto-bot-card
backend_url: "http://IP_Twojego_Serwera:8080"
pairs:
  - BTCUSDC
  - ETHUSDC
```
5. **API (wybrane)**:
   - `GET /health`
   - `POST /start` `{ "pairs":["BTCUSDC","ETHUSDC"], "autotrade": true }`
   - `POST /stop`
   - `POST /order/buy` `{ "pair":"BTCUSDC", "quote_amount_usd":50 }`
   - `POST /order/sell` `{ "pair":"BTCUSDC" }` lub `{ "pair":"BTCUSDC", "package_id":123 }`
   - `GET /config` / `PUT /config`
   - `GET /pair-config` / `PUT /pair-config` (np. `{ "pair":"BTCUSDC", "risk_level":7, "allowed":true }`)
   - `GET /logs`, `GET /alerts`, `DELETE /alerts`
   - `GET /market/history?pair=BTCUSDC&limit=100`

## Uwaga
- **Autotrade** działa tylko, gdy `running==true` (Start) i `autotrade==true`.  
- **Lookback** *week/month* używa kluczy `klines 1h` – na testnecie może brakować kompletnych danych; wówczas strategia kupna skupi się na downtrend/EMA.
- Brak eksportu CSV (zgodnie z Twoją prośbą).
