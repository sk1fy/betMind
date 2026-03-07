# Issue 1: Инициализация проекта betMind

## Описание

Создание базовой структуры проекта betMind для анализа и предсказания CS2 матчей.

## Задачи

- [x] Инициализировать структуру проекта
- [x] Создать документацию (README, ROADMAP, PRD)
- [x] Настроить play-scraper (web scraping)
- [x] Настроить predictor-v2 (prediction system)
- [x] Создать docs/ с knowledge base и ADR
- [x] Настроить .gitignore

## Acceptance Criteria

- Структура проекта соответствует документации
- Оба компонента готовы к запуску
- Документация актуальна

## Технические заметки

Первый релиз включает:
- play-scraper: Node.js + Playwright
- predictor-v2: Python + NumPy + TUI
- 5 моделей в ансамбле
- Genetic Algorithm оптимизатор
