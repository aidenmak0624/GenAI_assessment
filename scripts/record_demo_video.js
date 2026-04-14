const fs = require("fs");
const path = require("path");
const http = require("http");
const { spawn, spawnSync } = require("child_process");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const PORT = process.env.DEMO_RECORD_PORT || "8505";
const BASE_URL = `http://127.0.0.1:${PORT}`;
const OUTPUT_DIR = path.join(ROOT, "output", "playwright", "demo-video");
const RAW_VIDEO_DIR = path.join(OUTPUT_DIR, "raw");
const SERVER_LOG_PATH = path.join(OUTPUT_DIR, "server.log");
const FINAL_WEBM_PATH = path.join(OUTPUT_DIR, "techcorp-demo.webm");
const FINAL_MP4_PATH = path.join(OUTPUT_DIR, "techcorp-demo.mp4");
const UPLOAD_FILE = path.join(
  ROOT,
  "demo_assets",
  "upload_pdfs",
  "single",
  "beaconshield_device_protection_policy.pdf",
);

function loadDotEnv() {
  if (process.env.OPENAI_API_KEY) {
    return;
  }

  const envPath = path.join(ROOT, ".env");
  if (!fs.existsSync(envPath)) {
    return;
  }

  const contents = fs.readFileSync(envPath, "utf8");
  for (const line of contents.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) {
      continue;
    }
    const [rawKey, ...rest] = trimmed.split("=");
    const key = rawKey.trim();
    const value = rest.join("=").trim().replace(/^['"]|['"]$/g, "");
    if (!(key in process.env)) {
      process.env[key] = value;
    }
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function sanitizeName(value) {
  return value.replace(/[^a-z0-9_-]+/gi, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
}

async function waitForServer(url, timeoutMs = 300_000) {
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeoutMs) {
    const isReady = await new Promise((resolve) => {
      const req = http.get(url, (res) => {
        res.resume();
        resolve(res.statusCode && res.statusCode < 500);
      });
      req.on("error", () => resolve(false));
      req.setTimeout(3000, () => {
        req.destroy();
        resolve(false);
      });
    });

    if (isReady) {
      return;
    }

    await sleep(1000);
  }

  throw new Error(`Timed out waiting for app at ${url}`);
}

function startDemoServer() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const logStream = fs.createWriteStream(SERVER_LOG_PATH, { flags: "w" });
  const child = spawn("python", ["tests/e2e/run_app.py"], {
    cwd: ROOT,
    env: {
      ...process.env,
      PLAYWRIGHT_BASE_PORT: PORT,
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  child.stdout.pipe(logStream);
  child.stderr.pipe(logStream);
  child.on("exit", () => logStream.end());
  return child;
}

async function stopDemoServer(child) {
  if (!child || child.killed) {
    return;
  }

  child.kill("SIGTERM");
  await sleep(2000);

  if (!child.killed && child.exitCode === null) {
    child.kill("SIGKILL");
  }
}

async function showCaption(page, title, subtitle = "", durationMs = 2200) {
  await page.evaluate(
    ({ titleText, subtitleText }) => {
      const existing = document.getElementById("codex-demo-caption");
      if (existing) {
        existing.remove();
      }

      const wrapper = document.createElement("div");
      wrapper.id = "codex-demo-caption";
      wrapper.style.position = "fixed";
      wrapper.style.left = "24px";
      wrapper.style.top = "24px";
      wrapper.style.zIndex = "999999";
      wrapper.style.maxWidth = "760px";
      wrapper.style.padding = "18px 22px";
      wrapper.style.borderRadius = "16px";
      wrapper.style.background = "rgba(8, 12, 22, 0.88)";
      wrapper.style.border = "1px solid rgba(255,255,255,0.14)";
      wrapper.style.boxShadow = "0 18px 50px rgba(0,0,0,0.35)";
      wrapper.style.backdropFilter = "blur(8px)";
      wrapper.style.color = "#f8fafc";
      wrapper.style.fontFamily =
        "ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";

      const titleNode = document.createElement("div");
      titleNode.textContent = titleText;
      titleNode.style.fontSize = "28px";
      titleNode.style.fontWeight = "700";
      titleNode.style.lineHeight = "1.2";

      wrapper.appendChild(titleNode);

      if (subtitleText) {
        const subtitleNode = document.createElement("div");
        subtitleNode.textContent = subtitleText;
        subtitleNode.style.marginTop = "8px";
        subtitleNode.style.fontSize = "18px";
        subtitleNode.style.lineHeight = "1.4";
        subtitleNode.style.color = "rgba(241,245,249,0.88)";
        wrapper.appendChild(subtitleNode);
      }

      document.body.appendChild(wrapper);
    },
    { titleText: title, subtitleText: subtitle },
  );

  await page.waitForTimeout(durationMs);
  await page.evaluate(() => {
    const existing = document.getElementById("codex-demo-caption");
    if (existing) {
      existing.remove();
    }
  });
}

async function askInChat(page, question) {
  const chatInput = page.locator(
    'textarea[placeholder="Type your question here and press Enter..."]',
  );
  await chatInput.scrollIntoViewIfNeeded();
  await chatInput.fill(question);
  await chatInput.press("Enter");
}

function sourceToggleLocator(page) {
  return page
    .locator("summary, button, [role='button']")
    .filter({ hasText: /show sources/i });
}

async function getSourceButtonCount(page) {
  return sourceToggleLocator(page).count();
}

async function waitForNewSourceButton(page, previousCount, timeoutMs = 120_000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    const count = await getSourceButtonCount(page);
    if (count > previousCount) {
      return previousCount;
    }
    await page.waitForTimeout(500);
  }
  throw new Error("Timed out waiting for a completed assistant response with sources.");
}

async function expandSourceAtIndex(page, index, expectedText) {
  const buttons = sourceToggleLocator(page);
  const count = await buttons.count();
  if (count === 0 || index >= count) {
    return;
  }

  const button = buttons.nth(index);
  await button.scrollIntoViewIfNeeded();
  await button.click();

  if (expectedText) {
    await page.getByText(expectedText).last().waitFor({ timeout: 120_000 });
  }

  await page.waitForTimeout(2600);
}

async function waitForNoThinking(page, timeoutMs = 120_000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    const count = await page.getByText("Thinking...").count();
    if (count === 0) {
      return;
    }
    await page.waitForTimeout(400);
  }
  throw new Error("Timed out waiting for the assistant to finish responding.");
}

async function waitForVisibleText(page, pattern, timeoutMs = 120_000) {
  const startedAt = Date.now();
  const locator = page.getByText(pattern);

  while (Date.now() - startedAt < timeoutMs) {
    const count = await locator.count();
    for (let index = 0; index < count; index += 1) {
      const candidate = locator.nth(index);
      if (await candidate.isVisible().catch(() => false)) {
        return;
      }
    }
    await page.waitForTimeout(400);
  }

  throw new Error(`Timed out waiting for visible text: ${pattern}`);
}

async function saveFailureScreenshot(page, label) {
  const screenshotPath = path.join(
    OUTPUT_DIR,
    `${sanitizeName(label)}-failure.png`,
  );
  await page.screenshot({ path: screenshotPath, fullPage: true });
  return screenshotPath;
}

async function completeScene(page, options) {
  const {
    sceneName,
    trigger,
    routePattern,
    answerPattern,
    sourcePattern,
  } = options;

  const sourceCountBefore = await getSourceButtonCount(page);

  try {
    await trigger();
    await waitForVisibleText(page, routePattern, 120_000);
    await waitForVisibleText(page, answerPattern, 120_000);
    await waitForNoThinking(page, 120_000);
    const sourceIndex = await waitForNewSourceButton(page, sourceCountBefore, 30_000);
    await expandSourceAtIndex(page, sourceIndex, sourcePattern);
    console.log(`Scene complete: ${sceneName}`);
    await page.waitForTimeout(2500);
  } catch (error) {
    const screenshotPath = await saveFailureScreenshot(page, sceneName);
    throw new Error(`${sceneName} failed: ${error.message}. Screenshot: ${screenshotPath}`);
  }
}

async function main() {
  loadDotEnv();

  if (!process.env.OPENAI_API_KEY) {
    throw new Error("OPENAI_API_KEY is required to record the live demo.");
  }

  if (!fs.existsSync(UPLOAD_FILE)) {
    throw new Error(`Upload demo PDF not found: ${UPLOAD_FILE}`);
  }

  fs.rmSync(OUTPUT_DIR, { recursive: true, force: true });
  fs.mkdirSync(RAW_VIDEO_DIR, { recursive: true });

  const server = startDemoServer();
  let browser;
  let context;
  let page;
  let pageVideo;

  try {
    await waitForServer(BASE_URL);

    browser = await chromium.launch({ headless: true });
    context = await browser.newContext({
      viewport: { width: 1440, height: 1100 },
      recordVideo: {
        dir: RAW_VIDEO_DIR,
        size: { width: 1440, height: 1100 },
      },
    });

    page = await context.newPage();
    pageVideo = page.video();

    await page.goto(BASE_URL, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "🤖 TechCorp Customer Support AI" }).waitFor({
      timeout: 120_000,
    });
    console.log("Scene: app ready");

    await showCaption(
      page,
      "TechCorp Customer Support AI",
      "Multi-agent support assistant using SQL, RAG, LangGraph, and FastMCP",
      2600,
    );

    const clearChatButton = page.getByRole("button", { name: /clear chat history/i });
    if (await clearChatButton.count()) {
      await clearChatButton.click();
      await page.getByRole("heading", { name: "🤖 TechCorp Customer Support AI" }).waitFor();
      await page.waitForTimeout(1200);
    }

    await showCaption(
      page,
      "Part 1: Core functionality",
      "RAG, SQL, and hybrid reasoning across the seeded support system",
      2400,
    );

    await showCaption(
      page,
      "Demo 1: RAG over public policy PDFs",
      "Querying the seeded Best Buy policy document",
    );
    await completeScene(page, {
      sceneName: "demo-1-rag",
      trigger: () => askInChat(page, "Summarize Best Buy's return policy for most products."),
      routePattern: /RAG Agent \(Policy Documents\)/i,
      answerPattern: /15 days|30 days|45 days/i,
      sourcePattern: /bestbuy_return_exchange_policy\.pdf/i,
    });

    await showCaption(
      page,
      "Demo 2: Natural-language SQL over customer data",
      "Querying structured customer records from SQLite with natural language",
    );
    await completeScene(page, {
      sceneName: "demo-2-sql",
      trigger: () => askInChat(page, "How many Premium tier customers do we have?"),
      routePattern: /SQL Agent \(Customer Database\)/i,
      answerPattern: /11 Premium tier customers/i,
      sourcePattern: /\*\*SQL:\*\*|customers/i,
    });

    await showCaption(
      page,
      "Demo 3: Hybrid reasoning across SQL + policy documents",
      "Combining Ema's order history with the Best Buy return policy",
    );
    await completeScene(page, {
      sceneName: "demo-3-hybrid",
      trigger: () => askInChat(
        page,
        "Based on Best Buy's return policy, would Ema still qualify for a refund on her SmartDesk Hub?",
      ),
      routePattern: /Hybrid \(SQL \+ RAG Synthesis\)/i,
      answerPattern: /outside the documented return window|well beyond any typical return window|would not qualify/i,
      sourcePattern: /Source Details:|Customer Records:/i,
    });

    await showCaption(
      page,
      "Part 2: John's user workflow",
      "Upload a policy document, ask from the uploaded knowledge base, then check customer context",
      2400,
    );

    await showCaption(
      page,
      "Demo 4: Upload a new PDF and query it immediately",
      "BeaconShield policy is indexed at runtime and becomes searchable right away",
    );
    await page.locator('input[type="file"]').setInputFiles(UPLOAD_FILE);
    await page
      .getByText("Vector store updated with new documents!")
      .waitFor({ timeout: 180_000 });
    await page.waitForTimeout(1800);
    console.log("Scene: upload indexed");
    await completeScene(page, {
      sceneName: "demo-4-uploaded-policy",
      trigger: () => askInChat(page, "Summarize the BeaconShield device protection policy."),
      routePattern: /RAG Agent \(Policy Documents\)/i,
      answerPattern: /BeaconShield Standard|BeaconShield Plus|24 months/i,
      sourcePattern: /beaconshield_device_protection_policy\.pdf/i,
    });

    await showCaption(
      page,
      "Demo 5: John's customer lookup workflow",
      "Structured customer profile and ticket details from the SQL database",
    );
    await completeScene(page, {
      sceneName: "demo-5-john-sql-workflow",
      trigger: () => askInChat(
        page,
        "Give me a quick overview of customer Ema Johnson's profile and past support ticket details.",
      ),
      routePattern: /SQL Agent \(Customer Database\)/i,
      answerPattern: /Ema Johnson|Premium|ticket/i,
      sourcePattern: /\*\*SQL:\*\*|support_tickets|customers/i,
    });

    await showCaption(
      page,
      "Demo 6: FastMCP integration layer",
      "The same SQL, RAG, and hybrid backend can be reused by MCP-compatible clients",
      2800,
    );

    await showCaption(
      page,
      "Delivered capabilities",
      "Part 1: functionality. Part 2: John's workflow. Plus MCP integration.",
      2800,
    );

    await context.close();
    await browser.close();

    const rawVideoPath = await pageVideo.path();
    fs.copyFileSync(rawVideoPath, FINAL_WEBM_PATH);

    const ffmpegCheck = spawnSync("ffmpeg", ["-version"], { stdio: "ignore" });
    if (ffmpegCheck.status === 0) {
      const ffmpegResult = spawnSync(
        "ffmpeg",
        [
          "-y",
          "-i",
          FINAL_WEBM_PATH,
          "-c:v",
          "libx264",
          "-pix_fmt",
          "yuv420p",
          "-movflags",
          "+faststart",
          FINAL_MP4_PATH,
        ],
        { stdio: "ignore" },
      );
      if (ffmpegResult.status !== 0) {
        console.warn("ffmpeg conversion failed; keeping the .webm recording.");
      }
    }

    console.log(`Saved demo recording to ${FINAL_WEBM_PATH}`);
    if (fs.existsSync(FINAL_MP4_PATH)) {
      console.log(`Saved MP4 copy to ${FINAL_MP4_PATH}`);
    }
  } finally {
    if (context) {
      await context.close().catch(() => {});
    }
    if (browser) {
      await browser.close().catch(() => {});
    }
    await stopDemoServer(server);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
