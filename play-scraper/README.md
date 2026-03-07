# HLTV Web Scraper

Веб-скрапер для сбора данных о матчах CS:GO/CS2 с HLTV.org.

## Возможности

- **scrape-team.js** — извлечение данных о матче:
  - Названия команд
  - Мировые рейтинги
  - Veto-порядок (выбор/удаление карт)
  - Процент побед на каждой карте

- **scrape-team-stats.js** — извлечение статистики команды:
  - Название команды
  - Текущая выбранная карта
  - Детальная статистика (K/D, ADR и др.)

## Требования

- Node.js >= 18
- Google Chrome с удалённой отладкой

## Установка

```bash
cd play-scraper
npm install
```

## Использование

### 1. Запуск Chrome с удалённой отладкой

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

### 2. Открытие страницы HLTV

- Для `scrape-team.js`: откройте страницу матча на hltv.org
- Для `scrape-team-stats.js`: откройте страницу статистики команды

### 3. Запуск скрипта

```bash
node scrape-team.js
# или
node scrape-team-stats.js
```

## Вывод данных

Данные сохраняются в формате JSON:
- Папка: `{YYYY-MM-DD}/`
- Файл: `{team1-vs-team2}.json`

## Структура проекта

```
play-scraper/
├── scrape-team.js           # Основной скрипт сбора матчей
├── scrape-team-stats.js     # Скрипт сбора статистики
├── package.json             # Зависимости проекта
└── *.json                   # Примеры вывода
```

## Зависимости

- `@playwright/test` v1.57.0
- `playwright` v1.57.0
