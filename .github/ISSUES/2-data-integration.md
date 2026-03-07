# Issue 2: Интеграция play-scraper → predictor-v2

## Описание

Создать интеграцию между play-scraper (сбор данных) и predictor-v2 (предсказания). Необходимо реализовать конвертер данных и CLI команды для автоматического импорта.

## Задачи

- [ ] Создать конвертер данных `src/data/converter.py`
- [ ] Реализовать нормализацию названий команд и карт
- [ ] Добавить CLI команды в `src/main.py`
- [ ] Протестировать конвертацию на примере данных
- [ ] Запустить сбор 50-100 матчей через play-scraper
- [ ] Импортировать данные в predictor-v2
- [ ] Запустить первый GA для оптимизации параметров

## Acceptance Criteria

1. Конвертер преобразует JSON из play-scraper в формат HistoricalMatch
2. CLI команда `--convert <file>` работает корректно
3. После импорта данных запускается GA оптимизация
4. Параметры сохраняются в `parameters.json`

## Технические заметки

### Формат на входе (play-scraper)
```json
{
  "team1": { "name": "Navi", "ranking": 3 },
  "team2": { "name": "FaZe", "ranking": 5 },
  "maps": [...]
}
```

### Формат на выходе (predictor-v2)
```json
{
  "team1": "Navi",
  "team2": "FaZe",
  "team1_ranking": 3,
  "team2_ranking": 5,
  "team1_map_winrate": 0.65,
  ...
}
```

### CLI команды
```bash
# Конвертация файла
python src/main.py --convert data/raw/hltv.json

# Автоматически: сбор + конвертация
python src/main.py --scrape-and-import

# Отчёт о датасете
python src/main.py --dataset-report
```

## Roadmap

Milestone: **v1.1 - Data Integration**
