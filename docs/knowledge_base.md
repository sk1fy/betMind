# Knowledge Base — betMind

## Обзор проекта

**betMind** — система для анализа и предсказания исходов матчей Counter-Strike 2 (CS2).

## Компоненты

### play-scraper

Веб-скрапер для сбора данных с HLTV.org.

| Компонент | Технология |
|-----------|------------|
| Язык | JavaScript (Node.js) |
| Фреймворк | Playwright v1.57.0 |
| Браузер | Chromium через CDP |
| Выходные данные | JSON |

### predictor-v2

Система предсказания матчей.

| Компонент | Технология |
|-----------|------------|
| Язык | Python 3 |
| Алгоритмы | NumPy, Genetic Algorithm |
| UI | TUI (Terminal) |
| Хранилище | JSON |
| ML/AI | Нет (статистические модели) |

## Терминология

### CS2/Terms

| Термин | Описание |
|--------|----------|
| BO1/BO3/BO5 | Best of 1/3/5 — формат матча (до 1/3/5 побед) |
| Veto | Процесс выбора/удаления карт |
| Map Pool | Набор карт в ротации |
| WR (Win Rate) | Процент побед |
| Pistol Round | Первый раунд половины |
| Eco/Force Buy | Экономическая стратегия |
| HLTV | Основной статистический портал по CS |

### Модели (Ансамбль из 5 моделей)

| Модель | Вес | Подход |
|--------|-----|--------|
| SimulationModel | 30% | Monte-Carlo симуляция |
| BookmakerModel | 25% | Обратные вероятности от коэффициентов |
| ExpertModel | 20% | Эвристические правила |
| MomentumModel | 15% | Анализ трендов |
| ConsensusModel | 10% | Усреднение первых 4 моделей |

### Метрики

| Метрика | Описание |
|---------|----------|
| Accuracy | Процент правильных предсказаний победителя |
| Brier Score | Качество калибровки вероятностей |
| Calibration Error | Ошибка калибровки |
| EV (Expected Value) | Математическое ожидание ставки |

## Архитектура

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  play-scraper   │────▶│   Конвертер      │────▶│ predictor-v2    │
│  (HLTV data)   │     │  (converter)    │     │ (prediction)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │   GA Optimizer  │
                                              │ (parameter opt) │
                                              └─────────────────┘
```

## EngineParameters (13 tunable параметров)

| Параметр | Значение | Описание |
|----------|----------|----------|
| rank_weight | 0.0015 | Вес рейтинга команды |
| map_weight | 0.18 | Вес винрейта на карте |
| pick_bonus | 0.04 | Бонус за пик карты |
| form_multiplier | 0.025 | Множитель формы |
| odds_weight | 0.10 | Вес букмекерских коэффициентов |
| rounds_bias_multiplier | 0.015 | Коррекция предсказания раундов |
| pistol_weight | 1.0 | Вес пистолетных раундов |
| smooth_base | 5.0 | База сглаживания винрейта |
| day_form_variance | 0.06 | Дисперсия формы |
| force_buy_penalty | 0.15 | Штраф за force buy |
| eco_penalty | 0.22 | Штраф за eco раунд |
| tilt_resilience | 0.25 | Устойчивость к тильту |
| snowball_limit | 0.15 | Лимит снежного кома |

## Форматы данных

### HistoricalMatch

```python
{
    "team1": str,
    "team2": str,
    "team1_ranking": int,
    "team2_ranking": int,
    "map_name": str,
    "team1_map_winrate": float,
    "team2_map_winrate": float,
    "team1_form": float,
    "team2_form": float,
    "team1_odds": float,
    "team2_odds": float,
    "team1_pistol_wr": float,
    "team2_pistol_wr": float,
    "picked_by": str | None,
    "actual_winner": str,
    "actual_score_t1": int,
    "actual_score_t2": int
}
```

### TeamData

```python
{
    "name": str,
    "ranking": int,
    "form_score": float,  # 0.0 - 1.0 (явная оценка формы)
    "form_from_results": float,  # вычисляется из recent_results
    "odds": float,  # букмекерский коэффициент
    "map_stats": {
        "Mirage": {
            "wins": int,
            "losses": int,
            "rounds_won": int,
            "rounds_lost": int,
            "ct_wins": int,
            "t_wins": int,
            "pistol_wins": int,
            "pistol_total": int
        }
    },
    "recent_results": ["W", "L", "W", "W", "L"]
}
```

### MapStats

```python
{
    "map_name": str,
    "wins": int,
    "losses": int,
    "rounds_won": int,
    "rounds_lost": int,
    "ct_wins": int,
    "ct_losses": int,
    "t_wins": int,
    "t_losses": int,
    "pistol_wins": int,
    "pistol_total": int
}
```

## Genetic Algorithm Параметры

| Параметр | Значение |
|----------|----------|
| Population size | 100 |
| Generations | 150 |
| Elite size | 20 |
| Tournament size | 5 |
| Mutation rate | 0.2 |
| Crossover | BLX-alpha |

## Цель проекта

- **Точность:** 58-65%
- **Подход:** Статистические модели (без ML/XGBoost/LightGBM)
- **Оптимизация:** Genetic Algorithm для подбора параметров

## Ссылки

- [ROADMAP.md](../ROADMAP.md) — План развития
- [PRD.md](../PRD.md) — Требования к продукту
- [play-scraper/AGENTS.md](../play-scraper/AGENTS.md) — Документация скрапера
- [predictor-v2/AGENTS.md](../predictor-v2/AGENTS.md) — Документация predictor
