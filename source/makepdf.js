const { chromium } = require('playwright-core');
const path = require('path');

const EXE = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const htmlPath = path.resolve(process.argv[2] || 'report.html');
const outPath = path.resolve(process.argv[3] || 'mooi_report.pdf');

(async () => {
  const browser = await chromium.launch({
    executablePath: EXE,
    args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'],
  });
  const page = await browser.newPage();
  await page.goto('file://' + htmlPath, { waitUntil: 'networkidle' });
  // ensure fonts are ready
  await page.evaluate(() => document.fonts.ready);

  const footer = `
    <div style="width:100%; font-family:'NanumBarunGothic',sans-serif; font-size:7.5pt;
                color:#8a97a3; padding:0 13mm; display:flex; justify-content:space-between;
                align-items:center; -webkit-print-color-adjust:exact;">
      <span>무이성형외과 홈페이지 개편 점검 보고서 &amp; AI 검색 최적화 일정</span>
      <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
    </div>`;

  await page.pdf({
    path: outPath,
    format: 'A4',
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: footer,
    margin: { top: '13mm', bottom: '15mm', left: '13mm', right: '13mm' },
  });

  await browser.close();
  console.log('PDF written:', outPath);
})().catch(e => { console.error(e); process.exit(1); });
