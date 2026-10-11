# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Проект

**Dubai-Moscow Flight Finder** — приложение для поиска лучших авиабилетов Дубай ↔ Москва.
Репо: https://github.com/smikhovskiy/dubai-avia

## Команды

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск dev-сервера (из папки backend/)
uvicorn main:app --reload

# Сервер будет доступен на http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

## Структура

```
dubai-avia/
├── backend/
│   ├── main.py        # FastAPI app, CORS, /search и /health эндпоинты
│   ├── search.py      # Запрос к Tequila API, парсинг рейсов
│   ├── scoring.py     # Скоринг-движок (веса, нормализация, time_of_day)
│   └── enrichment.py  # Обогащение данными (задержки, комфорт) — не реализован
├── frontend/
│   └── index.html     # UI — не реализован
├── PLAN.md
└── CLAUDE.md
```

## Архитектура

`main.py` принимает запрос `/search` с параметрами дат (date_from, date_to, return_from, return_to), вызывает `fetch_flights()` из `search.py`, передаёт результат в `score_flights()` из `scoring.py`, возвращает отранжированный список.

**search.py**: строит запрос к Tequila API (`fly_from=DXB,AUH,DWC`, `fly_to=SVO,VKO,DME`, round trip), парсит ответ в структуру рейса с precomputed полями `_uae_airport_score` и `_msc_airport_score`.

**scoring.py**: нормализует цену и длительность across all results (min-max), считает stops/comfort из самих данных рейса, вычисляет `time_of_day` через `_time_of_day_score()`.

## API-ключи

Хранить в `.env` (не коммитить). Переменные:
- `TEQUILA_API_KEY` — Aviasales Tequila (поиск рейсов)
- `AVIATIONSTACK_API_KEY` — статистика задержек и отмен (для enrichment.py)

## Скоринг

```
score = 0.35 * price
      + 0.20 * duration
      + 0.20 * reliability
      + 0.15 * comfort
      + 0.10 * time_of_day
```

**time_of_day** = 0.4 × airport_score + 0.6 × departure_time_score

**Аэропорты ОАЭ:** DXB=1.0, AUH=0.7, DWC=0.3  
**Аэропорты Москвы:** SVO=1.0, VKO=0.7, DME=0.3

**Время суток:** будни (пн–пт) — рейсы после 18:00 получают 1.0, до 18:00 — 0.3; выходные — нейтрально (8–22 → 1.0, иначе 0.6).

**reliability**: прокси через остановки — `max(0.0, 1.0 - stops × 0.3)`. AviationStack (реальная статистика задержек) не подключён.

**comfort**: reliability × 0.8 если требуется пересадка багажа, иначе × 1.0.

## Правила работы

- Каждый этап из PLAN.md — отдельная ветка и PR
- Ветки: `feature/...`, `fix/...`
- Коммиты на английском, коротко
