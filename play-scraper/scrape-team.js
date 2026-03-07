// scrape-team.js
const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// Получаем сегодняшнюю дату в формате YYYY-MM-DD
function getTodaysDateFolder() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0'); // месяцы с 0
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

(async () => {
  try {
    const browser = await chromium.connectOverCDP('http://localhost:9222');
    const contexts = browser.contexts();
    let page;

    if (contexts.length > 0 && contexts[0].pages().length > 0) {
      page = contexts[0].pages()[0];
      console.log('➡️ Используем уже открытую вкладку...');
    } else {
      console.error('❌ Нет открытых вкладок. Откройте матч вручную в вашем Chrome.');
      return;
    }

    console.log('⏳ Ждём появления данных...');

    await Promise.all([
      page.waitForSelector('.team1-gradient .teamName', { timeout: 20000 }),
      page.waitForSelector('.team2-gradient .teamName', { timeout: 20000 }),
      page.waitForSelector('.teamRanking', { timeout: 15000 }),
      page.waitForSelector('.veto-box .padding > div', { timeout: 15000 }),
      page.waitForSelector('.map-stats-infobox-right > div[map-stats-infobox="wins"] .map-stats-infobox-maps', { timeout: 20000 })
    ]);

    // === Команды ===
    const team1Name = (await page.textContent('.team1-gradient .teamName'))?.trim() || 'Team 1';
    const team2Name = (await page.textContent('.team2-gradient .teamName'))?.trim() || 'Team 2';

    // === Рейтинги ===
    const rankingElements = await page.$$('.teamRanking');
    let rank1 = null, rank2 = null;
    if (rankingElements[0]) {
      const text1 = await rankingElements[0].textContent();
      const match1 = text1.match(/#(\d+)/);
      rank1 = match1 ? parseInt(match1[1], 10) : null;
    }
    if (rankingElements[1]) {
      const text2 = await rankingElements[1].textContent();
      const match2 = text2.match(/#(\d+)/);
      rank2 = match2 ? parseInt(match2[1], 10) : null;
    }

    // === Вето ===
    const vetoLines = await page.$$eval('.veto-box .padding > div', els =>
      els.map(el => el.textContent.trim())
    );

    // === Winrate по картам ===
    const rawMapStats = await page.$$eval(
      '.map-stats-infobox-right > div[map-stats-infobox="wins"] .map-stats-infobox-maps',
      maps => {
        return maps.map(map => {
          const mapName = map.querySelector('.mapname')?.textContent.trim() || 'Unknown';
          const winPercents = map.querySelectorAll('.map-stats-infobox-winpercentage a');
          const win1 = winPercents[0]?.textContent.trim() || '-';
          const win2 = winPercents[1]?.textContent.trim() || '-';
          return { map: mapName, win1, win2 };
        });
      }
    );

    // Преобразуем в читаемый формат
    const mapWinRates = rawMapStats.map(item => ({
      map: item.map,
      winRate: {
        [team1Name]: item.win1,
        [team2Name]: item.win2
      }
    }));

    // === Вывод ===
    console.log('\n✅ Команды:');
    console.log(`${team1Name} (World Rank: ${rank1 || '—'})`);
    console.log(`${team2Name} (World Rank: ${rank2 || '—'})`);

    console.log('\n✅ Вето:');
    vetoLines.forEach((line, i) => console.log(`${i + 1}. ${line}`));

    console.log('\n✅ Проценты побед по картам:');
    mapWinRates.forEach(({ map, winRate }) => {
      console.log(`${map}: ${team1Name} — ${winRate[team1Name]}, ${team2Name} — ${winRate[team2Name]}`);
    });

    // === Подготовка к сохранению ===
    const dateFolder = getTodaysDateFolder();
    if (!fs.existsSync(dateFolder)) {
      fs.mkdirSync(dateFolder);
      console.log(`📁 Создана папка: ${dateFolder}`);
    }

    // Безопасное имя файла
    const slug = `${team1Name.toLowerCase()}-vs-${team2Name.toLowerCase()}`;
    const safeSlug = slug.replace(/[^a-z0-9-]/g, '-').replace(/-+/g, '-');
    const filename = `${safeSlug}.json`;
    const filepath = path.join(dateFolder, filename);

    // === Структура JSON ===
    const result = {
      teams: {
        team1: {
          name: team1Name,
          worldRank: rank1
        },
        team2: {
          name: team2Name,
          worldRank: rank2
        }
      },
      veto: vetoLines,
      mapWinRates: mapWinRates // каждый элемент: { map, winRate: { "Team A": "...", "Team B": "..." } }
    };

    fs.writeFileSync(filepath, JSON.stringify(result, null, 2), 'utf8');
    console.log(`\n💾 Сохранено: ${filepath}`);

  } catch (error) {
    console.error('💥 Ошибка:', error.message);
    if (error.message.includes('waiting for selector')) {
      console.error('\n🔍 Не найдены данные на странице.');
      console.error('💡 Убедитесь, что матч полностью загружен в вашем Chrome.');
    }
  }
})();