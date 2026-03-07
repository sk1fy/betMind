// scrape-team-stats.js
const { chromium } = require('@playwright/test');

(async () => {
  try {
    const browser = await chromium.connectOverCDP('http://localhost:9222');
    const contexts = browser.contexts();
    let page;

    if (contexts.length > 0 && contexts[0].pages().length > 0) {
      page = contexts[0].pages()[0];
      console.log('➡️ Используем текущую вкладку...');
    } else {
      console.error('❌ Нет открытых вкладок. Откройте страницу статистики вручную.');
      return;
    }

    console.log('⏳ Ждём загрузки данных...');

    // Ждём появления ключевых элементов
    await Promise.all([
      page.waitForSelector('.tabs .selected', { timeout: 15000 }),
      page.waitForSelector('.stats-rows .stats-row', { timeout: 15000 }),
      page.waitForSelector('.stats-table tbody tr td:nth-child(2) a span', { timeout: 10000 })
    ]);

    // === Название команды ===
    const teamName = await page.textContent('.stats-table tbody tr td:nth-child(2) a span');
    if (!teamName) {
      throw new Error('Не удалось определить название команды');
    }

    // === Выбранная карта ===
    const mapName = await page.textContent('.tabs .selected');
    if (!mapName) {
      throw new Error('Не найдена выбранная карта');
    }

    // === Статистика ===
    const statsRows = await page.$$eval('.stats-rows .stats-row', rows => {
      return rows.map(row => {
        const label = row.querySelector('.strong')?.textContent.trim() || '';
        // Значение — второй дочерний текстовый узел или span
        const valueEl = row.querySelector('.strong + *') || row.childNodes[1];
        const value = valueEl?.textContent?.trim() || '';
        return { label, value };
      });
    });

    // === Вывод ===
    console.log(`\n📊 Команда: ${teamName}`);
    console.log(`🗺️ Карта: ${mapName}\n`);

    console.log('📈 Статистика:');
    statsRows.forEach(({ label, value }) => {
      console.log(`${label.padEnd(30)}: ${value}`);
    });

  } catch (error) {
    console.error('💥 Ошибка:', error.message);
    if (error.message.includes('waiting for selector')) {
      console.error('\n🔍 Не найдены элементы на странице.');
      console.error('💡 Убедитесь, что вы находитесь на странице вида:');
      console.error('   https://www.hltv.org/stats/lineup/map/... с таблицей матчей и статистикой');
    }
  }
})();