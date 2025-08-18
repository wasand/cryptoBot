#!/bin/bash
case "$1" in
  --demo)
    docker compose exec trading-bot python -m app.seed_example
    ;;
  --clean)
    docker compose down -v
    docker volume rm crypto-ha-bot-v8_db_data
    ;;
  --migrate)
    docker compose exec trading-bot python -m app.models
    ;;
  *)
    echo "Usage: $0 [--demo|--clean|--migrate]"
    exit 1
    ;;
esac