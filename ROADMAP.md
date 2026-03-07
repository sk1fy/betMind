# ROADMAP — betMind

> **См. также:** [Документация](../docs/) | [База знаний](../docs/knowledge_base.md) | [ADR](../docs/ADR/)

## Главный принцип проекта

Система строится на:
- статистических моделях
- симуляциях матчей
- качественных данных
- explainable predictions

**Цель — точность 58-65% без ML**

---

# Фаза 0 — Data First (самая важная)

Цель: получить **качественный dataset**.

## Задачи

### 0.1 Интеграция с play-scraper

**Текущее состояние:**
- `play-scraper/` — отдельный проект
- `predictor-v2/` — TUI приложение
- Нет интеграции между ними

**Архитектура интеграции:**

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ play-scraper  │────▶│   Конвертер      │────▶│ predictor-v2    │
│  (скрапер)      │     │  (новый скрипт)  │     │ (предсказания)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
   HLTV pages              hltv_raw.json           matches.json
```

**Задачи:**

#### 0.1.1 Расширение скрапера (play-scraper)

Добавить сбор дополнительных данных:

```javascript
// scrape-match.js — новый скрипт для сбора матчей

// Собираемые данные:
{
  "match_id": "2345678",
  "team1": {
    "name": "Navi",
    "ranking": 3,
    "players": ["s1mple", "electronic", ...],
    "map_stats": {
      "Mirage": { "wins": 45, "losses": 23, "winrate": 0.66 },
      ...
    },
    "recent_results": ["W", "W", "L", "W", "W"]
  },
  "team2": { ... },
  "maps": [
    { "name": "Mirage", "score": "16-12", "winner": "team1" },
    ...
  ],
  "format": "BO3",
  "date": "2024-01-15",
  "event": "BLAST Premier"
}
```

#### 0.1.2 Конвертер данных

Создать `src/data/converter.py`:

```python
# src/data/converter.py

import json
from datetime import datetime

class HLTVConverter:
    """Конвертирует вывод play-scraper в формат predictor-v2."""
    
    MAP_NAME_NORMALIZATION = {
        "de_mirage": "Mirage",
        "de_inferno": "Inferno", 
        "de_nuke": "Nuke",
        "de_ancient": "Ancient",
        "de_anubis": "Anubis",
        "de_vertigo": "Vertigo",
        "de_overpass": "Overpass",
    }
    
    TEAM_NAME_NORMALIZATION = {
        "navi": "Navi",
        "natus vincere": "Navi",
        "team vitality": "Vitality",
        ...
    }
    
    def convert_file(self, input_path: str, output_path: str):
        """Конвертировать файл."""
        with open(input_path) as f:
            raw_data = json.load(f)
        
        matches = []
        for item in raw_data:
            match = self.convert_match(item)
            matches.append(match)
        
        self.save_matches(matches, output_path)
    
    def convert_match(self, raw: dict) -> dict:
        """Конвертировать один матч."""
        return {
            "team1": self.normalize_team(raw["team1"]["name"]),
            "team2": self.normalize_team(raw["team2"]["name"]),
            "team1_ranking": raw["team1"]["ranking"],
            "team2_ranking": raw["team2"]["ranking"],
            "team1_form": self.calculate_form(raw["team1"]["recent_results"]),
            "team2_form": self.calculate_form(raw["team2"]["recent_results"]),
            "team1_map_winrate": self.get_map_winrate(raw["team1"], raw["map"]),
            "team2_map_winrate": self.get_map_winrate(raw["team2"], raw["map"]),
            "team1_pistol_wr": raw["team1"]["pistol_winrate"],
            "team2_pistol_wr": raw["team2"]["pistol_winrate"],
            "map_name": self.normalize_map(raw["map"]),
            "team["score"]["team1"],
            "1_score": rawteam2_score": raw["score"]["team2"],
            "actual_winner": raw["winner"],
            "picked_by": raw.get("picked_by"),
            "date": raw["date"],
        }
```

#### 0.1.3 CLI интеграция

Добавить команды в `src/main.py`:

```bash
# Сбор данных через play-scraper
python -m scraper --collect-matches --limit 100

# Конвертация
python src/main.py --convert data/raw/hltv.json

# Автоматически: сбор + конвертация
python src/main.py --scrape-and-import
```

#### 0.1.4 Скрипт сбора (wrapper)

Создать `scrape-matches.sh`:

```bash
#!/bin/bash
# Автоматический сбор матчей

# 1. Запустить Chrome с CDP
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 &

# 2. Открыть страницу HLTV matches
# (через AppleScript или Selenium)

# 3. Запустить скрапер
node scrape-matches.js

# 4. Конвертировать
python src/main.py --convert output.json
```

### 0.2 Сбор данных (как было)

### 0.2 Стандартизация данных

- Нормализация названий команд
- Единый список карт
- Удаление дубликатов

### 0.3 Data Validation

```python
# Валидация входящих данных
- rank ∈ [1..100]
- score ∈ [0..30]
- map ∈ [список карт]
- odds > 1.0
```

### 0.4 Dataset Report

Добавить CLI команду:

```bash
python src/main.py --dataset-report
```

Вывод:

```
Matches: 524
Teams: 38
Maps:
  Mirage: 112
  Inferno: 94
  Nuke: 87
  Ancient: 82
  Anubis: 76
  Vertigo: 45
  Overpass: 28
Average rounds: 24.1
Upset rate: 36%
```

---

# Фаза 1 — Базовая статистическая модель

Цель: создать **простую, объяснимую модель**.

## Основные факторы (5 штук)

Использовать только проверенные факторы:

```
1. rank_difference          # Разница рангов
2. map_winrate_difference  # Разница винрейта на карте
3. recent_form_difference  # Разница формы
4. pistol_round_difference # Разница пистолетных раундов
5. map_pick_bonus          # Бонус за пик карты
```

## Формула

```python
team_strength = (
    rank_factor * rank_weight +
    map_factor * map_weight +
    form_factor * form_weight +
    pistol_factor * pistol_weight +
    pick_bonus
)

# sigmoid для получения вероятности
probability = 1 / (1 + exp(-team_strength))
```

## Параметры по умолчанию

```json
{
  "rank_weight": 0.02,
  "map_weight": 0.15,
  "form_weight": 0.10,
  "pistol_weight": 0.08,
  "pick_bonus": 0.03
}
```

---

# Фаза 2 — Симуляция матчей (Monte Carlo)

Цель: перейти от одного прогноза к **распределению исходов**.

## Реализация

```python
def monte_carlo_simulation(team1, team2, map_name, num_simulations=5000):
    results = []
    
    for _ in range(num_simulations):
        # Симулировать каждый раунд
        t1_rounds, t2_rounds = simulate_map(team1_win_prob)
        
        results.append({
            't1_score': t1_rounds,
            't2_score': t2_rounds,
            'winner': team1 if t1_rounds > t2_rounds else team2
        })
    
    return analyze_results(results)
```

## Вывод

Пример результата:

```
Navi vs FaZe (Mirage)

Win Probability:
  Navi: 57%
  FaZe: 43%

Score Distribution:
  16-14: 18%
  16-12: 15%
  16-13: 14%
  16-10: 12%
  ...

Average Score: 15.8 - 13.2

Confidence Interval (95%):
  Navi wins: [52% - 62%]
```

---

# Фаза 3 — Симуляция Veto карт

Цель: учитывать **map veto process** в предсказаниях.

## Map Pool

```python
MAP_POOL = [
    "Mirage",
    "Inferno", 
    "Nuke",
    "Ancient",
    "Anubis",
    "Vertigo",
    "Overpass"
]
```

## Veto Алгоритм

```python
def simulate_veto(team1, team2):
    """
    Стандартный BO3 veto:
    T1 ban → T2 ban → T1 pick → T2 pick → T1 ban → T2 ban → decider
    """
    remaining_maps = MAP_POOL.copy()
    vetoed = []
    picked = []
    
    # ban, ban, pick, pick, ban, ban, decider
    for step in veto_order:
        if step == 'ban':
            team_bans = get_weakest_map(team, remaining_maps)
            vetoed.append(team_bans)
            remaining_maps.remove(team_bans)
        elif step == 'pick':
            team_picks = get_strongest_map(team, remaining_maps)
            picked.append((team, team_picks))
            remaining_maps.remove(team_picks)
        elif step == 'decider':
            decider = remaining_maps[0]
    
    return {
        'picked_maps': picked,
        'decider': decider,
        'vetoed': vetoed
    }
```

## Полное предсказание с veto

```
=== NAVI vs FAZE ===

Veto:
1. NAVI banned Vertigo
2. FAZE banned Overpass
3. NAVI picked Mirage ✓
4. FAZE picked Nuke
5. NAVI banned Anubis
6. FAZE banned Ancient
7. Decider: Inferno

Predicted Maps:
  Mirage: NAVI 57% (picked by NAVI)
  Nuke: FAZE 52%
  Inferno: NAVI 51% (decider)

Match Prediction:
  NAVI 2 - 1 FAZE
  Confidence: 58%
```

---

# Фаза 4 — Улучшение статистических факторов

Цель: добавить новые **значимые факторы**.

## 4.1 Momentum

```python
# Recent form с весами
def calculate_momentum(team):
    matches = team.last_10_matches
    
    # Последние 5 матчей важнее
    weights = [0.25, 0.20, 0.18, 0.17, 0.10, 0.05, 0.02, 0.01, 0.01, 0.01]
    
    weighted_sum = sum(w * m.result for w, m in zip(weights, matches))
    return weighted_sum
```

## 4.2 Map Pool Depth

```python
# Глубина пула карт
def calculate_pool_strength(team):
    strong_maps = 0
    weak_maps = 0
    
    for map_name, stats in team.map_stats.items():
        if stats.win_rate > 0.55:
            strong_maps += 1
        elif stats.win_rate < 0.40:
            weak_maps += 1
    
    return strong_maps - weak_maps
```

## 4.3 Team Stability

```python
# Стабильность состава
def calculate_stability(team):
    days_since_last = (now - team.last_match_date).days
    matches_per_week = team.matches_last_30_days / 4
    
    # Много игр = усталость
    fatigue_factor = min(matches_per_week * 0.02, 0.15)
    
    return 1.0 - fatigue_factor
```

## 4.4 Upset Potential

```python
# Потенциал сенсации
def calculate_underdog_potential(team):
    # Команды с высокой волатильностью
    if team.rank_volatility > 0.3:
        return 0.10  # Бонус андердогу
    return 0.0
```

---

# Фаза 5 — Backtesting

Цель: проверять модель на исторических данных.

## Реализация

```python
def backtest(train_until, test_after):
    """
    train_until: дата окончания train
    test_after: дата начала test
    """
    train_data = matches.where(date < train_until)
    test_data = matches.where(date >= test_after)
    
    results = []
    
    for match in test_data:
        prediction = predict(match)
        actual = match.winner
        
        results.append({
            'predicted': prediction,
            'actual': actual,
            'correct': prediction == actual
        })
    
    return calculate_metrics(results)
```

## Метрики

```python
{
    "winner_accuracy": 0.59,      # 59%
    "map_accuracy": 0.54,         # 54%
    "Brier_score": 0.21,         # Качество вероятностей
    "calibration_error": 0.06,    # Ошибка калибровки
    "roi": 1.15                  # ROI для betting
}
```

## Backtest Отчёт

```
=== Backtest Results ===

Period: 2024-01-01 to 2024-06-01
Train: 300 matches
Test: 100 matches

Winner Accuracy: 59%
Map Accuracy: 54%
Brier Score: 0.21
Calibration Error: 0.06

By Map:
  Mirage: 61%
  Nuke: 58%
  Inferno: 57%
  Ancient: 55%
  Anubis: 52%

By Rank Diff:
  Diff > 20: 68%
  Diff 10-20: 58%
  Diff < 10: 51%
```

---

# Фаза 6 — Value Betting

Цель: находить **value bets** (ставки с положительным ожиданием).

## Формула Expected Value

```
EV = (probability * odds) - 1
```

## Пример

```
Match: Navi vs FaZe
Odds: Navi 2.10, FaZe 1.75
Model Probability: Navi 57%

EV_Navi = (0.57 * 2.10) - 1 = 0.20 = +20%
EV_FaZe = (0.43 * 1.75) - 1 = -0.25 = -25%

RECOMMENDATION: BET NAVI
```

## Kelly Criterion

```python
def kelly_criterion(probability, odds):
    """
    Оптимальный размер ставки
    """
    b = odds - 1
    p = probability
    q = 1 - p
    
    kelly = (b * p - q) / b
    
    if kelly < 0:
        return 0  # Не ставить
    
    # Ограничить риск (пол-Kelly)
    return min(kelly / 2, 0.10)  # Max 10% банка
```

## Вывод Value Bets

```
=== Value Bets ===

Match: Spirit vs Vitality
Odds: 2.40
Model: 48%
EV: +15%

Match: Navi vs FaZe  
Odds: 2.10
Model: 47%
EV: -2% (no bet)

Match: G2 vs Liquid
Odds: 1.85
Model: 60%
EV: +11%
```

---

# Фаза 7 — Data Pipeline

Цель: автоматическое обновление данных.

## Pipeline Architecture

```
┌─────────────┐
│  Scraper    │  play-scraper
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Cleaner    │  Нормализация, валидация
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Updater    │  Добавление в dataset
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Stats      │  Пересчёт статистик
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Backtest   │  Проверка на новых данных
└─────────────┘
```

## Cron задание

```bash
# crontab -e
0 */6 * * * cd /path/to/predictor-v2 && python src/main.py --update
```

Запускать каждые 6 часов.

---

# Фаза 8 — API

## FastAPI Endpoints

```python
# src/api/app.py
from fastapi import FastAPI

app = FastAPI(title="CS2 Predictor API")

@app.post("/predict")
def predict(request: PredictRequest):
    """Предсказание матча"""
    return prediction

@app.get("/teams/{name}")
def get_team(name: str):
    """Статистика команды"""
    return team_stats

@app.get("/value-bets")
def get_value_bets():
    """Текущие value bets"""
    return value_bets

@app.get("/dataset-stats")
def get_dataset_stats():
    """Статистика датасета"""
    return stats

@app.get("/backtest")
def run_backtest(start: str, end: str):
    """Запустить backtest"""
    return results
```

## Примеры запросов

```bash
# Предсказание
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"team1": "Navi", "team2": "FaZe", "format": "BO3"}'

# Value bets
curl http://localhost:8000/value-bets

# Stats
curl http://localhost:8000/dataset-stats
```

---

# Фаза 9 — Улучшение интерфейса

## 9.1 Rich TUI

Заменить кастомный TUI на `rich`:

```python
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(title="Match Prediction")
table.add_column("Team", style="cyan")
table.add_column("Probability", style="green")
table.add_column("Factor", style="yellow")

table.add_row("Navi", "57%", "+6% rank")
table.add_row("FaZe", "43%", "-2% form")

console.print(table)
```

## 9.2 Аналитика в выводе

```
=== NAVI vs FAZE ===

Prediction Factors:
  +6.2%  Rank advantage (3 vs 8)
  +4.1%  Map advantage (Mirage: 62% vs 55%)
  -1.8%  Form (recent 5: 60% vs 65%)
  +0.8%  Pistol rounds
  +3.0%  Pick bonus (Mirage picked)

─────────────────────────
Final: NAVI 57% | FAZE 43%
Confidence: HIGH (58%)
```

## 9.3 Визуализация

- Графики формы команд
- Heatmap по картам
- Прогресс Monte Carlo

---

# Архитектурные улучшения

## Feature Cache

```python
from functools import lru_cache

@lru_cache(maxsize=500)
def get_team_stats(team_name):
    """Кешировать статистику команд"""
    return calculate_stats(team_name)
```

## Database (если >2000 матчей)

```python
# SQLite миграция
import sqlite3

# Когда данных станет много:
# 1. Создать таблицы
# 2. Мигрировать JSON → SQLite
# 3. Использовать индексы для быстрых запросов
```

## Explainable Predictions

Каждое предсказание показывает вклад каждого фактора:

```
Prediction Breakdown:
  Rank diff:        +6.2%
  Map winrate:      +4.1%
  Recent form:      -1.8%
  Pistol rounds:    +0.8%
  Pick bonus:       +3.0%
  ─────────────────
  Total:           +12.3%
  
  After sigmoid:    57%
```

---

# Приоритет реализации

| Приоритет | Фаза | Описание |
|-----------|------|----------|
| 1️⃣ | Фаза 0 | Data First — сбор 500+ матчей |
| 2️⃣ | Фаза 1 | Базовая статистическая модель |
| 3️⃣ | Фаза 2 | Monte Carlo симуляция |
| 4️⃣ | Фаза 3 | Map veto симуляция |
| 5️⃣ | Фаза 5 | Backtesting |
| 6️⃣ | Фаза 6 | Value betting |
| 7️⃣ | Фаза 7 | Data pipeline |
| 8️⃣ | Фаза 8 | API |
| 9️⃣ | Фаза 9 | UI улучшения |
| 🔟 | Фаза 4 | Дополнительные факторы |

---

# Ожидаемые результаты

| Этап | Точность |
|------|----------|
| baseline | 50-52% |
| статистика | 55% |
| симуляции | 57% |
| veto | 58-60% |
| data > 1000 | 60-63% |

---

# Главные факторы успеха

1. **Качественные данные** — 500+ матчей
2. **Симуляции матчей** — Monte Carlo
3. **Map veto modelling** — учёт процесса выбора карт
4. **Backtesting** — проверка на исторических данных

---

# Метрики успеха

| Метрика | Текущее | Цель |
|---------|---------|------|
| Winner accuracy | ~50-53% | 58-60% |
| Map accuracy | ~45% | 55% |
| Brier Score | — | <0.20 |
| Calibration error | — | <0.05 |
| Dataset size | 0 | 500+ |
| Prediction time | ~1s | <100ms |

---

# Что НЕ делать

| Идея | Причина |
|------|---------|
| XGBoost/LightGBM | Нужно 500+ матчей |
| Neural Network | Overkill для текущих данных |
| Платные Esports API | Дорого, сложно |
| Player-level stats | Требует много времени |
| Complex ensemble | Начать с простого |

---

# Зависимости между фазами

```
Фаза 0 ──> Фаза 1 ──> Фаза 2 ──> Фаза 3
              │              │
              │              ▼
              │         Фаза 5 (Backtesting)
              │              │
              ▼              ▼
Фаза 4 <── Фаза 6 (Value Betting)
              │
              ▼
         Фаза 7 (Pipeline)
              │
              ▼
         Фаза 8 (API)
              │
              ▼
         Фаза 9 (UI)
```
