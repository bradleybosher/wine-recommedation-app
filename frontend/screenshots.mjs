import { chromium } from 'playwright';
import { mkdir } from 'fs/promises';
import { join } from 'path';

const screenshotDir = 'screenshots';
await mkdir(screenshotDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage();

// Helper to take screenshot
async function screenshot(name) {
  const path = join(screenshotDir, `${name}.png`);
  await page.screenshot({ path, fullPage: true });
  console.log(`✓ ${path}`);
}

// Mock API responses using route interception
await page.route('**/inventory', async route => {
  if (route.request().method() === 'GET') {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        bottles: [],
        stale: false,
        ageHours: null
      })
    });
  } else {
    await route.continue();
  }
});

await page.route('**/upload-inventory', async route => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      count: 47,
      message: '47 bottles loaded from your cellar export.'
    })
  });
});

await page.route('**/upload-profile', async route => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      exportType: 'tasting_notes',
      message: 'Taste profile refined from tasting history.',
      tasteProfile: {
        preferredGrapes: ['Pinot Noir', 'Chardonnay', 'Nebbiolo'],
        preferredRegions: ['Burgundy', 'Barolo'],
        preferredStyles: ['earthy', 'mineral', 'structured'],
        avoidedStyles: ['oaky', 'jammy'],
        budgetMin: 40,
        budgetMax: 120
      }
    })
  });
});

await page.route('**/recommend', async route => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      profileMatchSummary: 'Strong match — your preference for structured Burgundian reds aligns well with this list.',
      listQualityNote: 'Good selection with 3 strong Burgundy options.',
      recommendations: [
        {
          rank: 1,
          wineName: 'Gevrey-Chambertin 1er Cru',
          producer: 'Rossignol-Trapet',
          vintage: 2019,
          region: 'Burgundy',
          price: 95,
          reasoning: 'Classic earthy Pinot Noir from your preferred region. The 2019 vintage matches your structured style preference.',
          confidence: 'high'
        },
        {
          rank: 2,
          wineName: 'Barolo Serralunga',
          producer: 'Giacomo Conterno',
          vintage: 2018,
          region: 'Piedmont',
          price: 110,
          reasoning: 'Nebbiolo-based with the tannic structure you favour. Price fits squarely within your typical spend range.',
          confidence: 'high'
        },
        {
          rank: 3,
          wineName: 'Chablis Premier Cru Montée de Tonnerre',
          producer: 'Raveneau',
          vintage: 2021,
          region: 'Chablis',
          price: 75,
          reasoning: 'Mineral-driven Chardonnay — hits your mineral style preference without the oak you avoid.',
          confidence: 'medium'
        }
      ]
    })
  });
});

try {
  console.log('📸 Capturing screenshots of wine recommendation app flow...\n');

  // Step 1: Navigate to app (triggers UploadFlow due to empty inventory)
  await page.goto('http://localhost:5173/', { waitUntil: 'domcontentloaded', timeout: 10000 });
  await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
  await page.waitForSelector('h2:has-text("Step 1")', { timeout: 5000 }).catch(() => console.log('Step 1 not found immediately'));
  await page.waitForTimeout(800);
  await screenshot('01-step1-cellar-form');
  console.log('Captured: Step 1 - Cellar Upload Form\n');

  // Step 2: Create a fake file and submit (simulate file upload)
  const fileInput = await page.$('input[type="file"]');
  console.log('File input found:', fileInput ? 'yes' : 'no');

  // We'll fill in the file input with a dummy file for visual purposes
  await page.evaluate(() => {
    // Create a fake file input event to show upload state
    const input = document.querySelector('input[type="file"]');
    if (input) {
      const dataTransfer = new DataTransfer();
      const file = new File(['dummy'], 'cellar.tsv', { type: 'text/plain' });
      dataTransfer.items.add(file);
      input.files = dataTransfer.files;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });

  await page.waitForTimeout(500);

  // Find and click submit button
  const submitBtn = await page.$('button:has-text("Upload & Continue")');
  if (submitBtn) {
    console.log('Clicking submit button...');
    await submitBtn.click();

    // Wait for loading state
    await page.waitForTimeout(1000);
    await screenshot('02-step1-loading');
    console.log('Captured: Step 1 - Loading State\n');

    // Wait for success state
    await page.waitForSelector('h2:has-text("Cellar Inventory Loaded")', { timeout: 5000 }).catch(() => console.log('Success state not found'));
    await page.waitForTimeout(500);
    await screenshot('03-step1-success');
    console.log('Captured: Step 1 - Success State\n');
  } else {
    console.log('Submit button not found');
  }

  // Step 3: Auto-advances to Step 2 after 1.5s - wait for it
  await page.waitForSelector('h2:has-text("Step 2")', { timeout: 8000 }).catch(() => console.log('Step 2 not found'));
  await page.waitForTimeout(500);
  await screenshot('04-step2-tasting-form');
  console.log('Captured: Step 2 - Tasting History Form\n');

  // Step 4: Skip profile upload to go to completion screen
  const skipBtn = await page.$('button:has-text("Skip for Now")');
  if (skipBtn) {
    console.log('Clicking skip button...');
    await skipBtn.click();

    // Wait for completion screen
    await page.waitForSelector('h1:has-text("Your Taste Profile is Ready")', { timeout: 5000 }).catch(() => console.log('Completion screen not found'));
    await page.waitForTimeout(500);
    await screenshot('05-completion-screen');
    console.log('Captured: Step 3 - Completion Screen\n');
  }

  // Step 5: Click "Analyze a Wine List" to go to recommendation screen
  const analyzeBtn = await page.$('button:has-text("Analyze a Wine List")');
  if (analyzeBtn) {
    console.log('Clicking analyze button...');
    await analyzeBtn.click();

    // Wait for recommendation screen
    await page.waitForSelector('h1:has-text("Wine Recommendations")', { timeout: 5000 }).catch(() => console.log('Recommendation screen not found'));
    await page.waitForTimeout(500);
    await screenshot('06-recommendation-screen');
    console.log('Captured: Recommendation Screen\n');
  }

  // Step 6: Fill in meal description and file for recommendation
  const mealInput = await page.$('textarea');
  if (mealInput) {
    await mealInput.fill('Grilled duck breast with cherry gastrique and roasted root vegetables');
  }

  // Add a file to the wine list uploader
  const fileInput2 = await page.$('input[type="file"]');
  if (fileInput2) {
    await page.evaluate(() => {
      const input = document.querySelector('input[type="file"]');
      if (input) {
        const dataTransfer = new DataTransfer();
        const file = new File(['dummy'], 'wine_list.pdf', { type: 'application/pdf' });
        dataTransfer.items.add(file);
        input.files = dataTransfer.files;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    await page.waitForTimeout(300);
  }

  await screenshot('07-recommendation-form-filled');
  console.log('Captured: Recommendation Form - Filled In\n');

  // Step 7: Submit recommendation request
  const getRecommendBtn = await page.$('button:has-text("Get Recommendations")');
  if (getRecommendBtn && !(await getRecommendBtn.isDisabled())) {
    console.log('Clicking get recommendations button...');
    await getRecommendBtn.click();

    // Wait for loading
    await page.waitForTimeout(1000);
    await screenshot('08-recommendation-loading');
    console.log('Captured: Recommendation - Loading State\n');

    // Wait for results
    await page.waitForSelector('h2:has-text("Top Recommendations")', { timeout: 5000 }).catch(() => console.log('Results not found'));
    await page.waitForTimeout(500);
    await screenshot('09-recommendation-results');
    console.log('Captured: Recommendation - Results\n');
  }

  console.log('\n✅ All screenshots captured successfully!');
  console.log(`📂 Check the "${screenshotDir}/" directory for all images.`);

} catch (error) {
  console.error('❌ Error capturing screenshots:', error.message);
} finally {
  await browser.close();
}
