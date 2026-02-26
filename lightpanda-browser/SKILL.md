---
name: lightpanda-browser
description: Use when you need Lightpanda headless browser automation on the cluster, especially Puppeteer CDP connections, scraping flows, and debugging Playwright connectOverCDP failures.
---

# lightpanda-browser: Lightpanda Headless Automation Expert

## Use this skill when

- Writing browser automation or web scraping scripts.
- The user asks to open a web page, test a UI, or fetch dynamic content.
- Encountering Playwright `connectOverCDP` errors or timeouts.
- Configuring a headless browser connection on the Co-lab or ism.la cluster.
- The user says things like:
  - "Connect Puppeteer to Lightpanda over CDP."
  - "Why is Playwright connectOverCDP failing with Lightpanda?"
  - "Use the existing Lightpanda container instead of launching Chromium."

## Do not use

- When the task requires screenshots, PDFs, file downloads, or WebSocket interception.
- When the task requires launching a separate local Chrome/Chromium process.
- When browser automation is not needed.

---

## Instructions

## Assumed context

This skill knows that a native ARM64 **Lightpanda** container is ALWAYS running on `crtr` (cooperator), exposing a Chrome DevTools Protocol (CDP) WebSocket endpoint at `ws://127.0.0.1:9222`.

**CRITICAL RULE:** Do NOT launch new Chrome or Chromium processes (do not use `puppeteer.launch()` or `chromium.launch()`). ALWAYS connect to the existing Lightpanda service.

---

## Architecture and service details

Lightpanda is a headless browser built from scratch (in Zig) for machines — not a Chromium fork.

- uses **10x less RAM** and runs **10x faster** than Chrome headless.
- lives in `ops/docker/lightpanda/`

| Property | Value |
|----------|-------|
| Protocol | Chrome DevTools Protocol (CDP) |
| Endpoint | `ws://127.0.0.1:9222/` |
| Image | `lightpanda/browser:latest` (arm64) |
| Container| `lightpanda` |

---

## Client compatibility (crucial)

| Client | Status | Notes |
|--------|--------|-------|
| **Puppeteer** | ✅ Recommended | Works flawlessly via `puppeteer.connect()`. Sends tiny 11KB payloads. |
| **Playwright** | ❌ BROKEN | `connectOverCDP()` fails with a WebSocket `101 Switching Protocols` handshake error. Playwright also sends massive 326KB payloads causing overhead. Do not use. |
| **Stagehand** | 🔶 Untested | Supported by Lightpanda docs, but bypasses Playwright's CDP handshake by using exact `cdpUrl`. Requires `ANTHROPIC_API_KEY`. |
| **gomcp** | ⚠️ Flaky | The `gomcp-mcp` service connects correctly, but drops the browser session after 10 seconds of inactivity. |

---

## Quick start: the verified pattern

### Puppeteer script (the only way)

Use `puppeteer-core` (not standard `puppeteer` which downloads a browser).

```javascript
import puppeteer from 'puppeteer-core';

(async () => {
  // 1. Connect to Lightpanda
  const browser = await puppeteer.connect({
    browserWSEndpoint: 'ws://127.0.0.1:9222/',
  });

  // 2. Create isolated context (Recommended)
  const context = await browser.createBrowserContext();
  const page = await context.newPage();

  // 3. Navigate to a real URL
  await page.goto('https://example.com', { timeout: 15000 });

  // 4. Do work
  const title = await page.title();
  const h1 = await page.$eval('h1', el => el.textContent);
  console.log('Title:', title, '| H1:', h1);

  // 5. Cleanup (Disconnect, DO NOT close the browser process)
  await page.close();
  await context.close();
  await browser.disconnect(); 
})();
```

---

## What not to do (anti-patterns)

- **Do NOT** use `page.setContent()`. It frequently causes timeouts. Always `page.goto()` a real URL.
- **Do NOT** use Playwright.
- **Do NOT** call `browser.close()`. This attempts to kill Lightpanda entirely, disrupting others. Use `browser.disconnect()`.
- **Do NOT** attempt to take screenshots or PDFs. Lightpanda does not support these layout-rendering CDP endpoints yet.
- **Do NOT** attempt file downloads or WebSocket interception.

---

## Troubleshooting

### "CouldntResolveHost" Error

If your script works but `goto()` fails, or you see `CouldntResolveHost` in `docker logs lightpanda`, Lightpanda cannot resolve DNS.
**Fix:** The `docker-compose.yml` for Lightpanda must explicitly contain a `dns:` block pointing to a resolver (e.g., `192.168.254.10` and `1.1.1.1`).

### Port 9222 Conflict

If Puppeteer gets a `404` or `Unexpected status 404 at /json/version`:

- The port `9222` might be stolen by Antigravity's own internal SSH tunnel port forwarding or a lingering `docker-proxy`.
- Check ownership: `sudo lsof -i :9222`
- Verify Lightpanda health: `curl -s http://127.0.0.1:9222/json/version` (Should return `webSocketDebuggerUrl`).

---

## Management

```bash
# Check status
docker ps --filter "name=lightpanda"

# Tail logs (incredibly useful for seeing CDP connections and DNS resolving info)
docker logs lightpanda --tail 50 -f
```
