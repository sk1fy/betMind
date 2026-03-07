# AGENTS.md — play-scraper

## Обзор проекта

Веб-скрапер на Node.js/Playwright для сбора данных о CS:GO матчах с HLTV.org. Подключается к запущенному Chrome через Chrome DevTools Protocol (CDP).

## Архитектура

### Основные файлы

| Файл | Назначение |
|------|------------|
| `scrape-team.js` | Сбор данных о матче (команды, рейтинги, veto, статистика карт) |
| `scrape-team-stats.js` | Сбор детальной статистики команды |
| `package.json` | Зависимости: `@playwright/test` v1.57.0 |

### Стек

- **Язык:** JavaScript (Node.js, CommonJS)
- **Фреймворк:** Playwright v1.57.0
- **Браузер:** Chromium через CDP
- **Node.js:** >= 18

## Работа с кодом

### Добавление нового скрапера

1. Создайте новый файл `scrape-{feature}.js`
2. Подключитесь к Chrome через CDP:
```javascript
const browser = await playwright.chromium.connectOverCDP('http://localhost:9222');
const context = browser.contexts()[0];
const page = context.pages()[0];
```

3. Используйте существующие селекторы из `scrape-team.js`:
```javascript
const team1Name = await page.locator('.team1-gradient .teamName').textContent();
const rankings = await page.locator('.teamRanking').allTextContents();
```

### Добавление новых полей для сбора

1. Откройте `scrape-team.js`
2. Добавьте новый локатор в соответствующей секции
3. Обновите структуру JSON-вывода

### Тестирование

Для тестирования изменений:
1. Запустите Chrome с `--remote-debugging-port=9222`
2. Откройте нужную страницу на HLTV
3. Запустите скрипт: `node scrape-team.js`

## Важные селекторы HLTV

```javascript
// Команды
'.team1-gradient .teamName'
'.team2-gradient .teamName'
'.teamRanking'

// Veto
'.veto-box .veto-map-name'
'.veto-box .pick'
'.veto-box .remove'

// Статистика карт
'.results-table .map-name'
'.results-team-row .win-percentage'
```

## Известные ограничения

- Требует запущенного Chrome с удалённой отладкой
- Работает только с одной активной вкладкой
- Зависит от структуры HTML HLTV (может сломаться при изменениях сайта)

## Интеграция с predictor-v2

Собранные данные могут использоваться в `predictor-v2`:
- Импортировать JSON в `src/data/historical/matches.json`
- Использовать для обучения генетического алгоритма
