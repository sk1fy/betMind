# Гайд: Как создать датасет для betMind

## Вариант 1: Использовать тестовые данные (быстро)

Уже создано 50 тестовых матчей. Запуск:

```bash
cd predictor-v2
python3 src/data/converter.py sample 100
```

---

## Вариант 2: Ручной сбор данных (рекомендуется для начала)

### Шаг 1: Запусти Chrome с отладкой

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

### Шаг 2: Открой страницу матча на HLTV

1. Зайди на https://www.hltv.org/matches
2. Выбери завершённый матч
3. Скопируй URL

### Шаг 3: Запусти скрапер

```bash
cd play-scraper
node scrape-team.js
```

Скрапер соберёт данные в JSON файл.

---

## Вариант 3: Автоматический сбор (для большого датасета)

### Структура данных

Создай файл `data.json` в формате:

```json
[
  {
    "team1": "Navi",
    "team2": "FaZe",
    "team1_ranking": 3,
    "team2_ranking": 5,
    "map_name": "Mirage",
    "team1_map_winrate": 0.65,
    "team2_map_winrate": 0.55,
    "team1_form": 0.7,
    "team2_form": 0.6,
    "team1_odds": 1.75,
    "team2_odds": 2.10,
    "team1_pistol_wr": 0.60,
    "team2_pistol_wr": 0.55,
    "picked_by": "Navi",
    "actual_winner": "Navi",
    "actual_score_t1": 16,
    "actual_score_t2": 12,
    "date": "2024-01-15"
  }
]
```

### Где брать данные

1. **HLTV.org** — основной источник
   - Рейтинги: https://www.hltv.org/teams
   - Статистика команд: https://www.hltv.org/stats/teams
   - Матчи: https://www.hltv.org/matches

2. **Liquipedia** — турнирные данные
   - https://liquipedia.net/counterstrike

### Минимальные поля для работающего GA

Для запуска генетического алгоритма нужны:

```json
{
  "team1": "Navi",
  "team2": "FaZe",
  "team1_ranking": 3,
  "team2_ranking": 5,
  "map_name": "Mirage",
  "team1_map_winrate": 0.65,
  "team2_map_winrate": 0.55,
  "team1_form": 0.7,
  "team2_form": 0.6,
  "team1_odds": 1.75,
  "team2_odds": 2.10,
  "team1_pistol_wr": 0.6,
  "team2_pistol_wr": 0.55,
  "picked_by": null,
  "actual_winner": "Navi",
  "actual_score_t1": 16,
  "actual_score_t2": 12
}
```

### Конвертация в predictor-v2

```bash
cd predictor-v2
python3 src/data/converter.py convert <input.json> src/data/historical/matches.json
```

---

## Вариант 4: Создать вручную (самый простой)

Создай файл `predictor-v2/src/data/historical/matches.json`:

```json
[
  {
    "team1": "Navi",
    "team2": "FaZe",
    "team1_ranking": 3,
    "team2_ranking": 5,
    "map_name": "Mirage",
    "team1_map_winrate": 0.65,
    "team2_map_winrate": 0.55,
    "team1_form": 0.7,
    "team2_form": 0.6,
    "team1_odds": 1.75,
    "team2_odds": 2.10,
    "team1_pistol_wr": 0.6,
    "team2_pistol_wr": 0.55,
    "picked_by": "Navi",
    "actual_winner": "Navi",
    "actual_score_t1": 16,
    "actual_score_t2": 12
  },
  {
    "team1": "Vitality",
    "team2": "G2",
    "team1_ranking": 4,
    "team2_ranking": 6,
    "map_name": "Nuke",
    "team1_map_winrate": 0.58,
    "team2_map_winrate": 0.62,
    "team1_form": 0.65,
    "team2_form": 0.68,
    "team1_odds": 2.0,
    "team2_odds": 1.85,
    "team1_pistol_wr": 0.55,
    "team2_pistol_wr": 0.6,
    "picked_by": "G2",
    "actual_winner": "G2",
    "actual_score_t1": 11,
    "actual_score_t2": 16
  }
]
```

**Минимум нужно 20-30 матчей** для запуска GA.

---

## Как проверить что данные загружены

```bash
cd predictor-v2
python3 -c "
from src.data.manager import DataManager
dm = DataManager()
matches = dm.load_historical_matches()
print(f'Загружено матчей: {len(matches)}')
for m in matches[:3]:
    print(f'  {m.team1} vs {m.team2}: {m.team1_ranking}-{m.team2_ranking}')
"
```

---

## Как запустить GA после сбора данных

```bash
cd predictor-v2
python3 -c "
from src.data.manager import DataManager
from src.core.optimizer import GeneticOptimizer, GeneticConfig

dm = DataManager()
matches = dm.load_historical_matches()
print(f'Матчей: {len(matches)}')

# Запуск GA (20 поколений для теста)
config = GeneticConfig(population_size=30, generations=20)
optimizer = GeneticOptimizer(config)
result = optimizer.run(matches)

print(f'Best fitness: {result[\"best_fitness\"]:.3f}')
print(f'Лучшие параметры: {result[\"best_params\"].to_dict()}')

# Сохранить
dm.save_parameters(result['best_params'])
print('Сохранено!')
"
```

---

## Где брать реальные данные (источники)

| Источник | URL | Что есть |
|----------|-----|----------|
| HLTV | hltv.org | Рейтинги, статистика, матчи |
| Liquipedia | liquipedia.net | Турниры, составы |
| HLTV Stats | hltv.org/stats | K/D, ADR, рейтинг |
| PGL | pgl.csgo.com | Турниры |

---

## Рекомендация

1. **Начни с варианта 4** — создай 20-30 матчей вручную
2. Запусти GA
3. Потом постепенно добавляй данные через скрапер
