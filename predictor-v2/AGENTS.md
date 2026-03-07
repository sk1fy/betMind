# AGENTS.md — predictor-v2

## Обзор проекта

TUI-приложение на Python для предсказания исходов матчей CS2. Использует ансамбль из 5 моделей и генетический алгоритм для оптимизации весов.

## Архитектура

### Стек

- **Язык:** Python 3
- **Зависимости:** NumPy >= 1.24.0
- **UI:** Кастомный TUI с использованием ANSI escape кодов
- **Данные:** JSON файлы

### Основные модули

| Модуль | Файл | Описание |
|--------|------|----------|
| Core | `src/core/engine.py` | PredictionEngine — основной движок предсказаний |
| Core | `src/core/models.py` | EnsemblePredictor — ансамбль из 5 моделей |
| Core | `src/core/optimizer.py` | GeneticOptimizer — генетический алгоритм |
| Core | `src/core/data_types.py` | Все dataclasses |
| Data | `src/data/manager.py` | DataManager — загрузка/сохранение JSON |
| UI | `src/ui/menus.py` | Главный цикл приложения |
| UI | `src/ui/input_forms.py` | Обработка ввода |
| UI | `src/ui/displays.py` | Функции отображения |
| UI | `src/ui/styles.py` | Константы стилей |

## Работа с кодом

### Добавление новой модели

1. Создайте класс модели в `src/core/models.py`
2. Наследуйтесь от базового класса
3. Реализуйте метод `predict()`
4. Добавьте в ансамбль с соответствующим весом

```python
class NewModel:
    def __init__(self, weight: float = 0.1):
        self.weight = weight
    
    def predict(self, team1: TeamData, team2: TeamData, 
                map_name: str, params: EngineParameters) -> MapPrediction:
        # Логика предсказания
        pass
```

### Изменение параметров модели

Параметры хранятся в `src/data/configs/parameters.json`:

```json
{
  "rank_weight": 0.0015,
  "map_weight": 0.18,
  "pick_bonus": 0.045,
  "form_multiplier": 0.025,
  "odds_weight": 0.1,
  "rounds_bias_multiplier": 0.015,
  "pistol_weight": 1.0,
  "smooth_base": 5.0,
  "day_form_variance": 0.06,
  "force_buy_penalty": 0.15,
  "eco_penalty": 0.22,
  "tilt_resilience": 0.25,
  "snowball_limit": 0.15
}
```

### Добавление исторических данных

Формат `src/data/historical/matches.json`:

```json
[
  {
    "team1": "Navi",
    "team2": "FaZe",
    "team1_rank": 3,
    "team2_rank": 5,
    "map": "Mirage",
    "team1_wins": 16,
    "team2_wins": 14,
    "date": "2024-01-15"
  }
]
```

### Настройка генетического алгоритма

Параметры GA в `src/core/optimizer.py`:

- Population size
- Number of generations
- Mutation rate
- Crossover method (BLX-alpha)
- Tournament size
- Elitism count

## Dataclasses (data_types.py)

```python
@dataclass
class TeamData:
    name: str
    world_rank: int
    recent_form: float  # 0.0 - 1.0
    odds: float

@dataclass
class MapStats:
    map_name: str
    team_wins: int
    team_losses: int
    avg_rounds: float

@dataclass
class MapPrediction:
    map_name: str
    team1_win_prob: float
    team2_win_prob: float
    predicted_score: tuple[int, int]
    confidence: float

@dataclass
class MatchPrediction:
    team1: str
    team2: str
    format: str  # BO1, BO3, BO5
    map_predictions: list[MapPrediction]
    over_under: dict
    confidence: float
```

## Известные ограничения

- TUI работает только в терминале с поддержкой ANSI
- JSON-хранилище не оптимизировано для больших объёмов данных
- Модели используют упрощённые эвристики, не полноценное ML

## Интеграция с play-scraper

1. Скрапер собирает данные с HLTV → JSON
2. Данные конвертируются в формат `matches.json`
3. Запускается GA-оптимизация для пересчёта весов
4. Модель использует обновлённые параметры

## Тестирование изменений

```bash
# Запуск основного приложения
python src/main.py

# Тестирование отдельных модулей
python -c "from src.core.models import EnsemblePredictor; print('OK')"
```
