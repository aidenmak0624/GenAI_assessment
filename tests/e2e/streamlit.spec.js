const { test, expect } = require("@playwright/test");

const hasLiveAi = Boolean(process.env.OPENAI_API_KEY);

async function openApp(page) {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "🤖 TechCorp Customer Support AI" }),
  ).toBeVisible();
}

async function clickExample(page, buttonName) {
  await page.getByRole("button", { name: buttonName }).click();
}

test("renders the Streamlit shell and verification controls", async ({ page }) => {
  await openApp(page);

  await expect(page.getByRole("heading", { name: "⚙️ Configuration" })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "🚀 Full Setup (DB + Public PDFs + Vector Store)" }),
  ).toBeVisible();
  await expect(page.getByText("DB Status", { exact: true })).toBeVisible();
  await expect(page.getByText("PDFs", { exact: true })).toBeVisible();
  await expect(page.getByText("Vector Store", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Summarize Best Buy's return policy for most products." }),
  ).toBeVisible();
  await expect(
    page.getByRole("textbox", {
      name: "Ask a question about customers, policies, or support...",
    }),
  ).toBeVisible();
});

test("requires an API key before a chat query can run", async ({ page }) => {
  test.skip(hasLiveAi, "This guardrail is only relevant when no live API key is provided.");

  await openApp(page);
  await clickExample(page, "Summarize Best Buy's return policy for most products.");

  await expect(
    page.getByText("Please enter your OpenAI API key in the sidebar."),
  ).toBeVisible();
});

test.describe("live AI verification", () => {
  test.skip(!hasLiveAi, "Set OPENAI_API_KEY to run live SQL/RAG/hybrid verification.");

  test("routes a policy question through the RAG agent", async ({ page }) => {
    await openApp(page);
    await clickExample(page, "Summarize Best Buy's return policy for most products.");

    await expect(page.getByText(/Routed to: .*RAG Agent/i)).toBeVisible({
      timeout: 120_000,
    });
    await expect(page.getByText(/Source:/i)).toBeVisible({ timeout: 120_000 });
    await expect(page.getByText(/bestbuy_return_exchange_policy\.pdf/i)).toBeVisible({
      timeout: 120_000,
    });
  });

  test("routes a customer question through the SQL agent", async ({ page }) => {
    await openApp(page);
    await clickExample(page, "How many Premium tier customers do we have?");

    await expect(page.getByText(/Routed to: .*SQL Agent/i)).toBeVisible({
      timeout: 120_000,
    });
    await expect(page.getByText(/Source:/i)).toBeVisible({ timeout: 120_000 });
    await expect(page.locator("code").filter({ hasText: "customers" })).toBeVisible({
      timeout: 120_000,
    });
    await expect(page.getByText(/\(\d+ rows? returned\)/i)).toBeVisible({
      timeout: 120_000,
    });
  });

  test("routes a blended question through the hybrid path", async ({ page }) => {
    await openApp(page);
    await clickExample(
      page,
      "Based on Best Buy's return policy, would Ema still qualify for a refund on her SmartDesk Hub?",
    );

    await expect(page.getByText(/Routed to: .*Hybrid/i)).toBeVisible({
      timeout: 120_000,
    });
    await expect(
      page.getByText(/15 days|30 days|45 days|not qualify|return window/i).first(),
    ).toBeVisible({ timeout: 120_000 });
  });
});
