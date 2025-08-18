# Crypto HA Bot Starter v6

Ten projekt to starter dla **Crypto Trading Bot** zintegrowanego z **Home Assistant**, obsługującego Binance Testnet oraz MariaDB.

## Funkcje w tej wersji
- Struktura kontenerów Docker (bot + baza MariaDB).
- Plik `.env.example` z podstawową konfiguracją.
- Skrypt `setup.sh` do łatwego uruchamiania.
- Przygotowane miejsce pod logikę bota w `bot/main.py`.

## Wymagania
- Docker i Docker Compose
- Konto na Binance (dla kluczy API, najlepiej Testnet)
- Linux/Ubuntu Server lub inny host z Dockerem

## Instalacja

1. Sklonuj repozytorium lub pobierz paczkę:
   ```bash
   scp crypto-ha-bot-starter-v6.zip user@host:/ścieżka/
   ```

2. Rozpakuj paczkę na serwerze:
   ```bash
   unzip crypto-ha-bot-starter-v6.zip -d ~/crypto-bot
   cd ~/crypto-bot
   ```

3. Skonfiguruj `.env`:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Uzupełnij:
   - `BINANCE_API_KEY` i `BINANCE_API_SECRET`
   - Dane dostępowe do bazy MariaDB (lub zostaw domyślne, jeśli używasz wbudowanej)

4. Uruchom bota:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

5. Sprawdź logi bota:
   ```bash
   docker compose logs -f bot
   ```

## Struktura katalogów
```
crypto-ha-bot-starter-v6/
├── bot/
│   └── main.py
├── .env.example
├── docker-compose.yml
├── setup.sh
```

## Następne kroki
- Implementacja logiki strategii handlowych.
- Dodanie integracji z Home Assistant Dashboard.
- Kolektory danych dla fiat, akcji i kryptowalut.
- System logów w bazie.

