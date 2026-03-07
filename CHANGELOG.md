# CHANGELOG — betMind

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- ROADMAP.md — стратегический план развития
- PROJECT.md — обзор проекта
- PRD.md — требования к продукту
- docs/ — документация проекта
  - knowledge_base.md — база знаний
  - ADR/ — Architecture Decision Records
  - README.md — индекс документации
- .gitignore — игнорируемые файлы
- play-scraper/ — репозиторий для сбора данных (переименован из playwright-test)
- predictor-v2/ — система предсказаний

### predictor-v2

#### Features
- TUI интерфейс с главным меню (8 пунктов)
- 5 моделей в ансамбле (Simulation, Bookmaker, Expert, Momentum, Consensus)
- Genetic Algorithm оптимизатор параметров
- DataManager для работы с JSON
- Quick и Detailed предсказания
- История предсказаний
- Экспорт в Markdown
- Статистика точности

#### Technical
- Параметризованный PredictionEngine
- 13 tunable параметров
- BLX-alpha crossover в GA
- Tournament selection
- Elitism preservation

### play-scraper

#### Features
- scrape-team.js — сбор данных о матчах (команды, рейтинги, veto, статистика карт)
- scrape-team-stats.js — сбор статистики команд (K/D, ADR)
- Подключение через Chrome DevTools Protocol

### Documentation

- docs/knowledge_base.md — термины, архитектура, форматы данных
- docs/ADR/001 — выбор технологического стека
- docs/ADR/002 — архитектура ансамбля моделей
- docs/ADR/003 — выбор хранилища данных
- docs/README.md — индекс документации

---

## [v1.0.0] — 2024-01-15

### Added

- Первый релиз predictor-v2
- Ансамбль из 5 моделей
- Генетический алгоритм оптимизации
- TUI интерфейс

---

## Соглашение о версионировании

Используем [Semantic Versioning](https://semver.org/lang/ru/):

- **MAJOR** — несовместимые изменения API
- **MINOR** — новая функциональность с обратной совместимостью
- **PATCH** — исправления багов

## Формат коммитов

Используем [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: добавить новую модель
fix: исправить баг в оптимизаторе
docs: обновить документацию
refactor: рефакторинг кода
chore: обновление зависимостей
```
