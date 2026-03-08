// scrape-team.js
const fs = require('fs');
const path = require('path');
const {
  getCliTargetUrl,
  openScraperPage,
  waitForOptionalSelector,
  waitForSelectorsWithRetry,
} = require('./browser-session');

// Получаем сегодняшнюю дату в формате YYYY-MM-DD
function getTodaysDateFolder() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0'); // месяцы с 0
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

(async () => {
  let closeSession = async () => {};

  try {
    const targetUrl = getCliTargetUrl();
    const { page, close, sourceDescription } = await openScraperPage({
      targetUrl,
      pageUrlMatcher: /hltv\.org\/matches\//i,
      description: 'страница матча HLTV',
    });
    closeSession = close;

    console.log(`➡️ ${sourceDescription}.`);
    if (targetUrl) {
      console.log(`🌐 Открываем: ${targetUrl}`);
    } else {
      console.log(`🌐 Используем вкладку: ${page.url()}`);
    }

    console.log('⏳ Ждём появления данных...');

    await waitForSelectorsWithRetry(page, [
      '.team1-gradient .teamName',
      '.team2-gradient .teamName',
      '.veto-box .padding > div',
    ], {
      attempts: 3,
      timeout: 20000,
    });

    const rankingsReady = await waitForOptionalSelector(page, '.teamRanking', 10000);
    const mapStatsReady = await waitForOptionalSelector(
      page,
      '.map-stats-infobox-right > div[map-stats-infobox="wins"] .map-stats-infobox-maps',
      12000
    );

    // === Команды ===
    const team1Name = (await page.textContent('.team1-gradient .teamName'))?.trim() || 'Team 1';
    const team2Name = (await page.textContent('.team2-gradient .teamName'))?.trim() || 'Team 2';

    // === Рейтинги ===
    const rankingElements = rankingsReady ? await page.$$('.teamRanking') : [];
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
    const rawMapStats = mapStatsReady
      ? await page.$$eval(
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
        )
      : [];

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
    if (mapWinRates.length === 0) {
      console.log('Нет блока winrate по картам. Матч может быть загружен не полностью или HLTV отдал неполную страницу.');
    } else {
      mapWinRates.forEach(({ map, winRate }) => {
        console.log(`${map}: ${team1Name} — ${winRate[team1Name]}, ${team2Name} — ${winRate[team2Name]}`);
      });
    }

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
      console.error('💡 Передайте прямой URL матча, например: node scrape-team.js https://www.hltv.org/matches/...');
    }
  } finally {
    await closeSession();
  }
})();
