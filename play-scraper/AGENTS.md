# AGENTS.md — play-scraper

## Обзор проекта

Веб-скрапер на Node.js/Playwright для сбора данных о CS:GO матчах с HLTV.org. Подключается к запущенному Chrome через Chrome DevTools Protocol (CDP).

## Архитектура

### Основные файлы

| Файл | Назначение |
|------|------------|
| `browser-session.js` | Подключение к Chrome/CDP, запуск локального браузера, выбор нужной вкладки, retry ожиданий |
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
2. Используйте общий helper `browser-session.js`, а не прямой доступ к `contexts()[0].pages()[0]`:
```javascript
const { getCliTargetUrl, openScraperPage } = require('./browser-session');

const targetUrl = getCliTargetUrl();
const { page } = await openScraperPage({
  targetUrl,
  pageUrlMatcher: /hltv\.org\/matches\//i,
  description: 'страница матча HLTV',
});
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
1. Предпочтительно передавайте прямой URL: `node scrape-team.js https://www.hltv.org/matches/...`
2. Если нужен уже открытый Chrome, запустите его с `--remote-debugging-port=9222`
3. Проверьте сценарии:
   - URL передан аргументом
   - URL не передан, но нужная вкладка уже открыта
   - часть необязательных блоков страницы не загрузилась с первого раза

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

- Если не передан URL и нет доступного CDP, локальный запуск браузера зависит от наличия системного Chrome или Playwright browsers
- Зависит от структуры HTML HLTV (может сломаться при изменениях сайта)

## Интеграция с predictor-v2

Собранные данные могут использоваться в `predictor-v2`:
- Импортировать JSON в `src/data/historical/matches.json`
- Использовать для обучения генетического алгоритма
