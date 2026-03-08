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

- **browser-session.js** — общий слой запуска браузера:
  - Подключение к уже открытому Chrome через CDP
  - Автоматический запуск локального Chrome/Chromium, если CDP недоступен
  - Выбор корректной вкладки HLTV или открытие URL из аргумента
  - Повторные ожидания селекторов при частичной загрузке страницы

## Требования

- Node.js >= 18
- Google Chrome с удалённой отладкой

## Установка

```bash
cd play-scraper
npm install
```

## Использование

### Вариант 1. Надёжный запуск с прямым URL

Такой запуск теперь предпочтителен: скрипт сам откроет нужную страницу и не зависит от "первой попавшейся" вкладки.

```bash
npm run scrape:match -- https://www.hltv.org/matches/...
npm run scrape:stats -- https://www.hltv.org/stats/...
```

### Вариант 2. Подключение к уже открытому Chrome через CDP

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

После этого можно либо открыть страницу вручную, либо всё так же передать URL в аргументе.

### Открытие страницы HLTV

- Для `scrape-team.js`: откройте страницу матча на hltv.org
- Для `scrape-team-stats.js`: откройте страницу статистики команды

### Запуск скрипта

```bash
node scrape-team.js
# или
node scrape-team-stats.js
```

С URL:

```bash
node scrape-team.js https://www.hltv.org/matches/...
node scrape-team-stats.js https://www.hltv.org/stats/...
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
├── browser-session.js       # Общая логика запуска браузера и выбора вкладки
├── package.json             # Зависимости проекта
└── *.json                   # Примеры вывода
```

## Зависимости

- `@playwright/test` v1.57.0
- `playwright` v1.57.0
