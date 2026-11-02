// Test przegladarkowy (Playwright, Chromium). Uruchamiany z backendem na PSYCHODELIC_TEST_URL.
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const BASE = process.env.PSYCHODELIC_TEST_URL ?? "http://127.0.0.1:8799";
const SHOTS = process.env.SHOTS_DIR ?? "/tmp/psy-shots";
fs.mkdirSync(SHOTS, { recursive: true });
const assert = (cond, msg) => { if (!cond) throw new Error("ASSERT: " + msg); };
const ok = (msg) => console.log("OK " + msg);

// Przegladarka: jawna sciezka (CHROMIUM_PATH) albo preinstalowany Chromium z sesji; bez pobierania.
const exe = process.env.CHROMIUM_PATH ?? "/opt/pw-browsers/chromium";
const browser = await chromium.launch(fs.existsSync(exe) ? { executablePath: exe } : {});
const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
await page.goto(BASE);

// 1. projekt
await page.getByPlaceholder("np. Mój projekt").fill("Mój projekt");
await page.getByRole("button", { name: "Utwórz projekt" }).click();
await page.getByText("zadania: 0").first().waitFor();
ok("utworzono projekt z UI");

// 2. plan ujec: wpisz czasy i sprawdz klatki
await page.locator("textarea").first().fill("The gardener stands still and watches the roses.");
await page.locator("textarea").nth(1).fill("He turns slowly toward the window; camera locked off.");
await page.getByRole("button", { name: "Sprawdź plan" }).click();
await page.getByText("Wynik · 2 ujęć").waitFor();
const frames = await page.locator("td.num .badge").allInnerTexts();
assert(frames.includes("124 kl.") && frames.includes("243 kl."), "klatki 124 i 243: " + frames);
ok("plan: 124 i 243 klatki (17n+5)");
await page.getByRole("button", { name: "Zapisz wszystkie prompty" }).click();
await page.getByText("Zapisano 2 promptów").waitFor();
await page.screenshot({ path: `${SHOTS}/01_plan.png`, fullPage: true });

// 3. H3: wybierz prompt, dodaj referencje, przygotuj komende (bez renderu)
await page.getByRole("button", { name: "H3 Extender" }).click();
await page.getByText("Plik promptu w projekcie").waitFor();
const promptSel = page.locator("select").first();
const opts = await promptSel.locator("option").allInnerTexts();
assert(opts.some((o) => o.includes("shot_01")), "prompt shot_01 zapisany z planu: " + opts);
ok("prompt z planu widoczny w H3");
await page.getByPlaceholder("np. ref_gsheet2.png").fill("ref_gsheet2.png");
await page.getByRole("button", { name: "Dodaj referencję" }).click();
await page.getByText("1 / 9").waitFor();
ok("referencja dodana, licznik 1 / 9");
await page.getByRole("button", { name: "Przygotuj komendę (bez renderu)" }).click();
await page.getByText("Gotowa komenda").waitFor();
const cmd = await page.locator("pre.cmd").first().innerText();
assert(cmd.includes("gen_extender_refine.py") && cmd.includes("REFS=ref_gsheet2.png"), "komenda: " + cmd);
assert((await page.getByText("NIE została uruchomiona").count()) > 0, "brak informacji o niewykonaniu");
ok("komenda przygotowana, informacja: nie uruchomiono");
await page.screenshot({ path: `${SHOTS}/02_h3.png`, fullPage: true });

// 4. status: render wylaczony
await page.getByRole("button", { name: "Stan systemu" }).click();
await page.getByText("Stan systemu").first().waitFor();
assert((await page.getByText("Render GPU: wyłączony").count()) > 0, "chip render wylaczony");
ok("status: render wylaczony");
await page.screenshot({ path: `${SHOTS}/03_status.png`, fullPage: true });

// 5. przeglad: rejestracja wariantu i decyzja NIE kasuje pliku
const root = await (await fetch(`${BASE}/api/projects-summary`)).json().then((l) => l[0].id);
const info = await (await fetch(`${BASE}/api/projects/${root}`)).json();
fs.mkdirSync(path.join(info.root_path, "renders"), { recursive: true });
const file = path.join(info.root_path, "renders", "v3b_1_new_only.mp4");
fs.writeFileSync(file, "fake-video");
await page.getByRole("button", { name: "Przegląd" }).click();
await page.getByPlaceholder("renders/shot_01_final.mp4").fill("renders/v3b_1_new_only.mp4");
await page.getByRole("button", { name: "Dodaj do przeglądu" }).click();
await page.getByText("Do oceny · 1").waitFor();
await page.getByRole("button", { name: "Odrzuć" }).click();
await page.getByText("Zdecydowane · 1").waitFor();
assert(fs.existsSync(file), "odrzucenie nie moze kasowac pliku");
ok("przegląd: odrzucenie zapisane, plik zachowany");
await page.screenshot({ path: `${SHOTS}/04_review.png`, fullPage: true });

// 6. oś: nakladajace sie klipy -> blad po stronie klienta i zablokowany zapis
await page.getByRole("button", { name: "Oś montażowa" }).click();
await page.getByRole("button", { name: "+ dodaj klip" }).click();
await page.getByRole("button", { name: "+ dodaj klip" }).click();
const srcInputs = page.locator('input[placeholder="renders/…mp4"]');
await srcInputs.nth(0).fill("renders/a.mp4");
await srcInputs.nth(1).fill("renders/b.mp4");
// klip b startuje w klatce 10, a klip a trwa 124 klatki -> nakladanie
await page.locator("tbody tr").nth(1).locator("td").nth(4).locator("input").fill("10");
await page.getByText(/nakładają się na osi/).first().waitFor();
assert(await page.getByRole("button", { name: "Zapisz oś" }).isDisabled(), "zapis osi powinien byc zablokowany przy nakladaniu");
ok("oś: nakładanie wykryte, zapis zablokowany");
await page.screenshot({ path: `${SHOTS}/05_timeline.png`, fullPage: true });

// 7. jezyk: przelacz na angielski i sprawdz napisy; sprawdzenie ComfyUI (serwer nieosiagalny = uczciwy komunikat)
await page.locator(".lang button", { hasText: "EN" }).click();
await page.locator(".tabs button", { hasText: "Timeline" }).waitFor();
assert((await page.locator(".tabs button", { hasText: "Oś montażowa" }).count()) === 0, "po EN nadal polski");
ok("jezyk: angielski przelaczony");
await page.locator(".tabs button", { hasText: "System status" }).click();
await page.getByRole("button", { name: "Check ComfyUI" }).click();
await page.getByText("ComfyUI does not respond").first().waitFor();
ok("ComfyUI: brak odpowiedzi pokazany uczciwie");
await page.locator(".lang button", { hasText: "PL" }).click();
await page.locator(".tabs button", { hasText: "Stan systemu" }).waitFor();
await page.screenshot({ path: `${SHOTS}/06_status_pl.png`, fullPage: true });
ok("jezyk: powrot do polskiego");

assert(errors.length === 0, "bledy w konsoli: " + errors.join(" | "));
await browser.close();
console.log("\nWszystkie testy przegladarki OK. Zrzuty: " + SHOTS);
