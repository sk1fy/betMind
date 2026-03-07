Ниже — полноценный **PRD (Product Requirements Document)**, идеи **улучшений** и **roadmap развития** для проекта predictor-v2. Я пишу так, как это обычно делают для реального ML/аналитического продукта.

---

# PRD — predictor-v2

**CS2 Match Outcome Prediction System**

## 1. Обзор продукта

**predictor-v2** — это терминальное приложение для прогнозирования исходов матчей **Counter-Strike 2**.
Система использует **ансамбль моделей и генетический алгоритм**, который оптимизирует веса моделей на основе исторических матчей.

Продукт ориентирован на:

* аналитиков киберспорта
* беттеров
* исследователей статистики матчей
* разработчиков моделей прогнозирования

---

# 2. Цели продукта

## Основные цели

1. **Прогнозирование исхода матчей CS2**
2. **Оценка вероятности победы**
3. **Предсказание счёта по картам**
4. **Автоматическая оптимизация параметров модели**
5. **Интерактивный анализ матчей через TUI**

---

# 3. Пользовательские сценарии

## 3.1 Аналитик

**Хочу:**

* ввести команды
* выбрать формат (BO1 / BO3 / BO5)
* увидеть вероятности побед
* получить прогноз по картам

**Результат:**

```
NAVI vs FAZE

Mirage:
NAVI 55% | FAZE 45%
Predicted: 16-13

Inferno:
NAVI 49% | FAZE 51%

Match Prediction:
NAVI 2 - 1 FAZE
Confidence: 0.64
```

---

## 3.2 Беттер

**Хочу:**

* сравнить модель с коэффициентами букмекеров
* найти value bets

**Результат**

```
Bookmaker Odds:
NAVI 1.85
FAZE 2.05

Model Probability:
NAVI 58%

Value Bet Detected
```

---

## 3.3 Разработчик модели

**Хочу:**

* добавлять новые модели
* тестировать их влияние
* оптимизировать веса

---

# 4. Функциональные требования

## 4.1 Предсказание матчей

Система должна:

* принимать входные данные:

```
team1
team2
rank
recent_form
map
odds
```

* выдавать:

```
probability
score prediction
confidence
```

---

## 4.2 Ансамбль моделей

Система использует **5 моделей**.

Каждая модель возвращает:

```
MapPrediction
```

Итог:

```
ensemble_prediction =
sum(model_prediction * weight)
```

---

## 4.3 Генетическая оптимизация

GeneticOptimizer должен:

* оптимизировать веса моделей
* минимизировать prediction error

Параметры:

| параметр        | описание           |
| --------------- | ------------------ |
| population_size | количество решений |
| generations     | поколений          |
| mutation_rate   | шанс мутации       |
| crossover       | BLX-alpha          |
| elitism         | лучшие решения     |

---

## 4.4 Исторические данные

Файл:

```
src/data/historical/matches.json
```

Используется для:

* обучения
* оптимизации
* тестирования модели

---

## 4.5 TUI интерфейс

Основные меню:

```
1 Predict Match
2 Run Genetic Optimization
3 View Model Weights
4 View Historical Stats
5 Exit
```

---

# 5. Нефункциональные требования

## Производительность

* предсказание < **50 ms**
* GA оптимизация < **2 минут**

---

## Надёжность

* JSON должен валидироваться
* fallback параметры

---

## Масштабируемость

Архитектура должна позволять:

* добавлять новые модели
* менять алгоритмы оптимизации

---

# 6. Метрики успеха

Основная метрика:

```
Prediction Accuracy
```

Дополнительные:

| метрика               | цель  |
| --------------------- | ----- |
| Match winner accuracy | > 60% |
| Map score MAE         | < 2.5 |
| Calibration error     | < 0.1 |

---

# 7. Ограничения

1️⃣ Нет настоящего ML
(только эвристики)

2️⃣ Нет live данных

3️⃣ JSON не подходит для больших датасетов

---

# 8. Архитектура (упрощённо)

```
           +------------------+
           | Historical Data  |
           +--------+---------+
                    |
                    v
          +--------------------+
          | Genetic Optimizer  |
          +---------+----------+
                    |
                    v
             +-------------+
             | Ensemble    |
             | Predictor   |
             +------+------+
                    |
                    v
            +---------------+
            | Prediction    |
            | Engine        |
            +-------+-------+
                    |
                    v
                TUI UI
```

---

# Улучшения проекта

Вот **самые важные улучшения**, которые реально сделают проект сильнее.

---

# 1. Реальные ML модели

Сейчас:

```
heuristics
```

Лучше:

* **XGBoost**
* **LightGBM**
* **Logistic Regression**
* **Neural Network**

Фичи:

```
team_rank_diff
map_winrate
recent_kd
player_rating
head_to_head
economy_stats
```

---

# 2. Автоматический сбор данных

Интеграция с:

* HLTV
* Liquipedia
* Esports API

Скрапер:

```
playwright
```

Pipeline:

```
scraper → dataset → model
```

---

# 3. База данных вместо JSON

Сейчас:

```
JSON
```

Лучше:

```
SQLite
или
DuckDB
```

Это ускорит:

* аналитику
* обучение
* статистику

---

# 4. Симуляция матчей (Monte Carlo)

Очень мощная функция.

Вместо одного прогноза:

```
simulate 10000 matches
```

Получим:

```
win probability
round distribution
map probability
```

---

# 5. Value betting модуль

Добавить:

```
expected value calculation
```

Формула:

```
EV = (probability * odds) - 1
```

Вывод:

```
+EV bets
```

---

# 6. Map veto simulation

CS2 сильно зависит от **veto процесса**.

Добавить:

```
map pool
ban logic
pick logic
```

---

# 7. Player level statistics

Сейчас:

```
team level
```

Лучше:

```
player stats
rating
impact
clutches
entry success
```

---

# 8. Улучшенный UI

TUI можно сделать лучше через:

```
rich
textual
```

Получится:

* таблицы
* графики
* прогресс бары

---

# 9. Backtesting система

Проверка модели:

```
train on 2023
test on 2024
```

Метрики:

```
ROI
accuracy
log loss
```

---

# 10. API режим

Сделать:

```
REST API
```

пример:

```
POST /predict
```

---

# Возможный Roadmap

## Phase 1 — Stabilization (1–2 недели)

Цель: стабилизировать проект

* [ ] unit tests
* [ ] JSON validation
* [ ] logging
* [ ] config system
* [ ] CLI args

---

## Phase 2 — Data Upgrade (2–3 недели)

* [ ] HLTV scraper
* [ ] player statistics
* [ ] map pool stats
* [ ] database migration (SQLite)

---

## Phase 3 — Model Upgrade (3–4 недели)

* [ ] logistic regression
* [ ] XGBoost model
* [ ] feature engineering
* [ ] model evaluation

---

## Phase 4 — Simulation (2 недели)

* [ ] Monte Carlo match simulation
* [ ] map veto simulation
* [ ] round distribution model

---

## Phase 5 — UX Upgrade (1–2 недели)

* [ ] rich TUI
* [ ] charts
* [ ] better match display

---

## Phase 6 — Betting tools (2 недели)

* [ ] odds integration
* [ ] EV detection
* [ ] bet recommendations

---

# Потенциал проекта

Если развить проект, он может стать:

### 1️⃣ полноценным аналитическим движком CS2

или

### 2️⃣ системой value betting

или

### 3️⃣ ML playground для esports analytics

---

💡 Если хочешь, я могу ещё сделать:

* **архитектуру predictor v3 (очень мощную)**
* **ML feature list для CS2**
* **схему базы данных**
* **как сделать точность >70%** (реально достижимо).
