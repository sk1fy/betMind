# betMind Project

Комплексная система для анализа и предсказания матчей CS:GO/CS2.

## Обзор

Проект состоит из двух взаимосвязанных приложений:

1. **play-scraper** — сбор данных с HLTV.org
2. **predictor-v2** — предсказание исходов матчей

## Структура проекта

```
betMind/
├── play-scraper/           # Web scraping (Node.js)
│   ├── README.md
│   ├── AGENTS.md
│   ├── scrape-team.js
│   ├── scrape-team-stats.js
│   └── package.json
│
├── predictor-v2/          # Prediction system (Python)
│   ├── README.md
│   ├── AGENTS.md
│   ├── requirements.txt
│   ├── src/
│   │   ├── main.py
│   │   ├── core/        # Engine, models, optimizer
│   │   ├── data/        # JSON storage
│   │   └── ui/          # TUI interface
│   └── plan.md
│
└── PROJECT.md            # Этот файл
```

## Workflow

```
┌─────────────────┐     ┌─────────────────┐
│  HLTV.org      │     │   User Input    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ play-scraper    │────▶│ predictor-v2    │
│ (scraper)       │     │ (prediction)    │
└─────────────────┘     └─────────────────┘
         │                       │
         ▼                       ▼
    matches.json          predictions.json
```

## Технологический стек

| Компонент | Технология |
|-----------|------------|
| Скрапер | Node.js, Playwright |
| ML/Алгоритмы | Python, NumPy |
| UI | TUI (Terminal) |
| Данные | JSON |

## Установка и запуск

### play-scraper

```bash
cd play-scraper
npm install

# Запуск Chrome с удалённой отладкой
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Запуск скрипта
node scrape-team.js
```

### predictor-v2

```bash
cd predictor-v2
pip install -r requirements.txt
python src/main.py
```

## Связь между проектами

| play-scraper → | predictor-v2 |
|----------------|--------------|
| Собранные матчи | Исторические данные для GA |
| Статистика команд | Детальные предсказания |
| Veto-информация | Анализ пиков |

## Разработка

См. отдельные файлы AGENTS.md в каждой директории для деталей:
- `play-scraper/AGENTS.md`
- `predictor-v2/AGENTS.md`

## Roadmap

- [ ] Автоматический импорт данных из play-scraper в predictor-v2
- [ ] API для интеграции между проектами
- [ ] Расширение списка источников данных
- [ ] Web-интерфейс для predictor-v2
- [ ] Docker-контейнеризация

## Документация

| Файл | Описание |
|------|----------|
| [ROADMAP.md](ROADMAP.md) | Стратегический план развития |
| [PRD.md](PRD.md) | Требования к продукту |
| [CHANGELOG.md](CHANGELOG.md) | История изменений |
| [docs/knowledge_base.md](docs/knowledge_base.md) | База знаний |
| [docs/ADR/](docs/ADR/) | Architecture Decision Records |

## Текущий статус

- ✅ predictor-v2: TUI приложение работает
- ✅ Ансамбль из 5 моделей реализован
- ✅ Генетический алгоритм оптимизации реализован
- ⚠️ play-scraper: требуется расширение функциональности
- ⚠️ Интеграция: не реализована
