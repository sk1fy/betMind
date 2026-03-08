const { chromium } = require('@playwright/test');
const fs = require('fs');

const DEFAULT_CDP_URL = process.env.PLAY_SCRAPER_CDP_URL || 'http://127.0.0.1:9222';
const DEFAULT_TIMEOUT = Number(process.env.PLAY_SCRAPER_TIMEOUT || 45000);

function getCliTargetUrl() {
  const args = process.argv.slice(2);

  for (const arg of args) {
    if (arg.startsWith('--url=')) {
      return arg.slice('--url='.length);
    }
  }

  const positionalUrl = args.find(arg => !arg.startsWith('--'));
  return positionalUrl || null;
}

function describeSource(source) {
  switch (source) {
    case 'cdp':
      return 'подключились к уже запущенному Chrome через CDP';
    case 'chrome':
      return 'запустили локальный Google Chrome через Playwright';
    case 'chromium':
      return 'запустили локальный Chromium через Playwright';
    default:
      return 'используем Playwright';
  }
}

function flattenPages(browser) {
  return browser.contexts().flatMap(context => context.pages());
}

function matchesPage(page, matcher) {
  if (!matcher) {
    return true;
  }

  const currentUrl = page.url();

  if (matcher instanceof RegExp) {
    return matcher.test(currentUrl);
  }

  return currentUrl.includes(matcher);
}

function pickExistingPage(browser, matcher) {
  const pages = flattenPages(browser).filter(page => page.url() !== 'about:blank');

  const matchedPages = pages.filter(page => matchesPage(page, matcher));
  if (matchedPages.length > 0) {
    return matchedPages[matchedPages.length - 1];
  }

  if (!matcher && pages.length > 0) {
    return pages[pages.length - 1];
  }

  return null;
}

async function tryConnectOverCDP() {
  try {
    const browser = await chromium.connectOverCDP(DEFAULT_CDP_URL);
    return { browser, source: 'cdp', ownedBrowser: false };
  } catch (error) {
    return { browser: null, error };
  }
}

async function tryLaunchLocalBrowser() {
  const headless = process.env.PLAY_SCRAPER_HEADLESS === '1';
  const chromeExecutablePath = findChromeExecutablePath();

  if (chromeExecutablePath) {
    try {
      const browser = await chromium.launch({
        executablePath: chromeExecutablePath,
        headless,
      });

      return { browser, source: 'chrome', ownedBrowser: true };
    } catch (chromeError) {
      try {
        const browser = await chromium.launch({ headless });
        return { browser, source: 'chromium', ownedBrowser: true, fallbackError: chromeError };
      } catch (chromiumError) {
        throw buildLaunchError(chromeError, chromiumError);
      }
    }
  }

  try {
    const browser = await chromium.launch({ headless });
    return { browser, source: 'chromium', ownedBrowser: true };
  } catch (chromiumError) {
    throw buildLaunchError(null, chromiumError);
  }
}

async function getOrCreateContext(browser) {
  const existingContext = browser.contexts()[0];
  if (existingContext) {
    return existingContext;
  }

  return browser.newContext();
}

async function openScraperPage({ targetUrl, pageUrlMatcher, description }) {
  const cdpSession = await tryConnectOverCDP();
  const session = cdpSession.browser ? cdpSession : await tryLaunchLocalBrowser();

  const context = await getOrCreateContext(session.browser);
  let page = pickExistingPage(session.browser, pageUrlMatcher);

  if (!page) {
    page = await context.newPage();
  }

  if (targetUrl) {
    await page.goto(targetUrl, {
      waitUntil: 'domcontentloaded',
      timeout: DEFAULT_TIMEOUT,
    });
  } else if (page.url() === 'about:blank') {
    throw new Error(
      `Не найдена открытая ${description}. Передайте URL первым аргументом или через --url=.`
    );
  }

  await page.bringToFront();
  await page.waitForLoadState('domcontentloaded', { timeout: DEFAULT_TIMEOUT }).catch(() => {});

  return {
    browser: session.browser,
    context,
    page,
    close: async () => {
      if (session.ownedBrowser) {
        await session.browser.close();
      }
    },
    source: session.source,
    sourceDescription: describeSource(session.source),
    cdpError: cdpSession.error || null,
    fallbackError: session.fallbackError || null,
  };
}

async function waitForSelectorsWithRetry(page, selectors, options = {}) {
  const {
    attempts = 3,
    timeout = DEFAULT_TIMEOUT,
    reloadBetweenAttempts = true,
    retryDelayMs = 1200,
  } = options;

  let lastError;

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      for (const selector of selectors) {
        await page.waitForSelector(selector, { timeout, state: 'visible' });
      }

      return;
    } catch (error) {
      lastError = error;

      if (attempt === attempts) {
        break;
      }

      if (reloadBetweenAttempts && page.url() !== 'about:blank') {
        await page.reload({
          waitUntil: 'domcontentloaded',
          timeout,
        }).catch(() => {});
      }

      await page.waitForTimeout(retryDelayMs);
    }
  }

  throw lastError;
}

async function waitForOptionalSelector(page, selector, timeout = 10000) {
  try {
    await page.waitForSelector(selector, { timeout, state: 'visible' });
    return true;
  } catch {
    return false;
  }
}

function findChromeExecutablePath() {
  const configuredPath = process.env.PLAY_SCRAPER_BROWSER_PATH;
  if (configuredPath && fs.existsSync(configuredPath)) {
    return configuredPath;
  }

  const candidates = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ];

  return candidates.find(candidate => fs.existsSync(candidate)) || null;
}

function buildLaunchError(chromeError, chromiumError) {
  const details = [];

  if (chromeError) {
    details.push(`system Chrome: ${chromeError.message}`);
  }

  if (chromiumError) {
    details.push(`Playwright Chromium: ${chromiumError.message}`);
  }

  return new Error(
    `Не удалось запустить браузер. Попробуйте запустить Chrome с --remote-debugging-port=9222 или установите Playwright browsers через npx playwright install.\n${details.join('\n')}`
  );
}

module.exports = {
  DEFAULT_CDP_URL,
  DEFAULT_TIMEOUT,
  getCliTargetUrl,
  openScraperPage,
  waitForOptionalSelector,
  waitForSelectorsWithRetry,
};
