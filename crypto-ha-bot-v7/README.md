# Crypto HA Bot v7

Bot tradingowy dla Binance (Testnet/Prod) z dashboardem Home Assistant i logami w MariaDB.

## Szybki start
1. Skonfiguruj użytkownika i bazę w **core-mariadb** (HA).
2. Skopiuj `.env.example` do `.env` i ustaw:
   - `BINANCE_API_KEY` i `BINANCE_API_SECRET` (TESTNET)
   - `DB_*` z Twojego HA (host zwykle `core-mariadb`)
   - `DEFAULT_PAIRS=BTCUSDC,ETHUSDC`
3. Uruchom:
   ```bash
   docker compose up -d --build
   ```
4. Test połączeń:
   ```bash
   docker compose exec trading-bot python -m app.check_connection
   ```

## API
- `GET /health`
- `POST /start` body: `{ "pairs": ["BTCUSDC","ETHUSDC"] }`
- `POST /stop`
- `GET /logs?limit=100`
- `GET /alerts?limit=100`
- `DELETE /alerts` (czyści alerty)

## Home Assistant
Wklej zawartość `bot/app/ha_dashboard/rest_sensors.yaml` do Twojej konfiguracji HA (sensors i rest_command),
a `bot/app/ha_dashboard/ui_config.yaml` jako osobny widok Lovelace (dodaj przez Raw configuration editor).

## Ustawienia
- Interwał pracy: `BOT_INTERVAL_SEC=300` (5m)
- Alerty PnL (%): `ALERT_PNL_POSITIVE=10`, `ALERT_PNL_NEGATIVE=-5`
- Przełącznik testnet/produkcyjny: `BINANCE_TESTNET=true/false`

## Uwaga
Ta wersja zawiera prostą strategię referencyjną i kolektor danych.
Przed włączeniem trybu produkcyjnego **upewnij się** że parametry ryzyka i limity są zgodne z Twoimi wymaganiami.
