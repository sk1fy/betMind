// scrape-team-stats.js
const {
  getCliTargetUrl,
  openScraperPage,
  waitForOptionalSelector,
  waitForSelectorsWithRetry,
} = require('./browser-session');

(async () => {
  let closeSession = async () => {};

  try {
    const targetUrl = getCliTargetUrl();
    const { page, close, sourceDescription } = await openScraperPage({
      targetUrl,
      pageUrlMatcher: /hltv\.org\/stats\//i,
      description: 'страница статистики HLTV',
    });
    closeSession = close;

    console.log(`➡️ ${sourceDescription}.`);
    if (targetUrl) {
      console.log(`🌐 Открываем: ${targetUrl}`);
    } else {
      console.log(`🌐 Используем вкладку: ${page.url()}`);
    }

    console.log('⏳ Ждём загрузки данных...');

    await waitForSelectorsWithRetry(page, [
      '.stats-rows .stats-row',
    ], {
      attempts: 3,
      timeout: 20000,
    });

    await waitForOptionalSelector(page, '.tabs .selected', 10000);

    const teamNameSelector = await waitForOptionalSelector(
      page,
      '.context-item-name',
      5000
    )
      ? '.context-item-name'
      : '.stats-table tbody tr td:nth-child(2) a span';

    // === Название команды ===
    const teamName = await page.textContent(teamNameSelector);
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
      console.error('   https://www.hltv.org/stats/... или передайте URL: node scrape-team-stats.js https://www.hltv.org/stats/...');
    }
  } finally {
    await closeSession();
  }
})();
