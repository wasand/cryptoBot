# Crypto HA Bot v8.5 – Kompletny bot tradingowy (Docker + MariaDB + Home Assistant)

Wersja zawiera:
- **Autotrade**: Kupno/sprzedaż pakietów z parametrami: min profit %, histereza %, drawdown %, min transakcji/h, mnożnik w downtrendzie, lookback (day/week/month).
- **Kolektor danych**: Kryptowaluty (5m, EMA12/26, MACD, ATR14), FX (USD→PLN/EUR/GBP/CHF, NBP), akcje (BLK, IVV, VOO, yfinance).
- **Dashboard HA**: Start/stop, autotrade, kup/sprzedaj, ustawienia strategii, wykresy (ceny, PnL USD/PLN), logi, alerty.
- **ML**: Tabela `ml_features`, kontener `ml-worker` (Granger causality placeholder).
- **DB**: MariaDB (`core-mariadb`), tabele z `batch_id` dla synchronizacji.

## Uruchomienie
1. **Baza**:
   ```sql
   GRANT ALL PRIVILEGES ON crypto_bot_db.* TO 'crypto_bot'@'%' IDENTIFIED BY 'TwojeHaslo123';
   FLUSH PRIVILEGES;