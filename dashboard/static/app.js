const form = document.querySelector("#params-form");
const resetButton = document.querySelector("#reset-button");
const statusEl = document.querySelector("#status");
const canvas = document.querySelector("#price-chart");
const ctx = canvas.getContext("2d");
const pythonChartsEl = document.querySelector("#python-charts");

let defaults = {};
let lastPriceSeries = [];

function resizeCanvas() {
  const ratio = window.devicePixelRatio || 1;
  const cssWidth = canvas.clientWidth || 980;
  const cssHeight = canvas.clientHeight || 360;
  canvas.width = Math.round(cssWidth * ratio);
  canvas.height = Math.round(cssHeight * ratio);
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
}

let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    resizeCanvas();
    drawChart(lastPriceSeries);
  }, 150);
});

function descriviErrore(error) {
  if (error instanceof TypeError) return "Server non raggiungibile";
  return error.message || "Errore imprevisto";
}

const numericInputs = form.querySelectorAll("[data-number-input]");
const percentageGroups = [
  { id: "trader-types", label: "Tipi di trader" },
  { id: "news", label: "Notizie", enabledWhen: () => isTraderActive("noise") },
];
const PERCENT_TOLERANCE = 0.000001;
const traderToggles = form.querySelectorAll("[data-trader-toggle]");
const simpleToggles = form.querySelectorAll("[data-simple-toggle]");

function normalizeDecimalValue(value) {
  return String(value).replace(",", ".");
}

function readNumericAttribute(input, attributeName, fallback) {
  const value = Number(input.dataset[attributeName]);
  return Number.isFinite(value) ? value : fallback;
}

function countDecimals(value) {
  const normalizedValue = String(value);
  const decimalPart = normalizedValue.split(".")[1];
  return decimalPart ? decimalPart.length : 0;
}

function formatSteppedValue(value, input) {
  const precision = Math.min(countDecimals(input.dataset.step || "1"), 12);
  return precision > 0 ? value.toFixed(precision).replace(/\.?0+$/, "") : String(Math.round(value));
}

function stepInput(input, direction) {
  const step = readNumericAttribute(input, "step", 1);
  const min = readNumericAttribute(input, "min", -Infinity);
  const max = readNumericAttribute(input, "max", Infinity);
  const current = Number(normalizeDecimalValue(input.value));
  const baseValue = Number.isFinite(current) ? current : Number(defaults[input.name] ?? min ?? 0);
  const nextValue = Math.min(Math.max(baseValue + direction * step, min), max);

  input.value = formatSteppedValue(nextValue, input);
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

function readInputNumber(input) {
  const value = Number(normalizeDecimalValue(input.value));
  return Number.isFinite(value) ? value : null;
}

function clampInputValue(input) {
  const value = readInputNumber(input);
  if (value === null) return;
  const min = readNumericAttribute(input, "min", -Infinity);
  const max = readNumericAttribute(input, "max", Infinity);
  const clamped = Math.min(Math.max(value, min), max);
  input.value = formatSteppedValue(clamped, input);
}

function isTraderActive(traderType) {
  const toggle = form.querySelector(`[data-trader-toggle="${traderType}"]`);
  return !toggle || toggle.checked;
}

function validatePercentageGroups() {
  const messages = [];

  percentageGroups.forEach(({ id, label, enabledWhen }) => {
    const allInputs = [...form.querySelectorAll(`[data-percent-group="${id}"]`)];
    const status = form.querySelector(`[data-percent-status="${id}"]`);

    if (enabledWhen && !enabledWhen()) {
      allInputs.forEach((input) => {
        input.classList.remove("is-invalid");
        input.setAttribute("aria-invalid", "false");
      });
      if (status) {
        status.textContent = "";
        status.classList.remove("is-invalid");
      }
      return;
    }

    const inputs = allInputs.filter((input) => !input.disabled);
    const values = inputs.map(readInputNumber);
    const hasNoActiveInputs = inputs.length === 0;
    const hasInvalidValue = values.some((value) => value === null);
    const total = values.reduce((sum, value) => sum + (value ?? 0), 0);
    const isValid = !hasNoActiveInputs && !hasInvalidValue && Math.abs(total - 100) <= PERCENT_TOLERANCE;
    const totalText = formatSteppedValue(total, { dataset: { step: "0.01" } });
    const totalLabel = id === "trader-types" ? "Totale attivo" : "Totale";

    allInputs.forEach((input) => {
      const isActive = !input.disabled;
      input.classList.toggle("is-invalid", isActive && !isValid);
      input.setAttribute("aria-invalid", String(isActive && !isValid));
    });

    if (status) {
      status.textContent = hasNoActiveInputs
        ? `${label}: attiva almeno una categoria`
        : isValid
          ? `${totalLabel}: ${totalText}%`
          : `${totalLabel}: ${totalText}% - deve essere 100%`;
      status.classList.toggle("is-invalid", !isValid);
    }

    if (!isValid) {
      messages.push(
        hasNoActiveInputs
          ? `${label}: attiva almeno una categoria`
          : `${label}: totale ${totalText}%, deve essere 100%`
      );
    }
  });

  return { valid: messages.length === 0, messages };
}

function syncTraderControls() {
  traderToggles.forEach((toggle) => {
    const traderType = toggle.dataset.traderToggle;
    const isActive = toggle.checked;
    const percentInput = form.querySelector(`[data-trader-percent="${traderType}"]`);
    const card = form.querySelector(`[data-trader-card="${traderType}"]`);

    if (percentInput) {
      percentInput.disabled = !isActive;
      percentInput.classList.remove("is-invalid");
      percentInput.setAttribute("aria-invalid", "false");
      const stepperButtons = percentInput.parentElement?.querySelectorAll(".stepper-button") || [];
      stepperButtons.forEach((button) => {
        button.disabled = !isActive;
      });
    }
    if (card) {
      card.classList.toggle("is-disabled", !isActive);
    }
  });

  const noiseActive = isTraderActive("noise");
  const newsSubmenu = form.querySelector("[data-noise-submenu]");
  const newsInputs = form.querySelectorAll("[data-noise-setting]");

  newsInputs.forEach((input) => {
    input.disabled = !noiseActive;
    input.classList.remove("is-invalid");
    input.setAttribute("aria-invalid", "false");
    const stepperButtons = input.parentElement?.querySelectorAll(".stepper-button") || [];
    stepperButtons.forEach((button) => {
      button.disabled = !noiseActive;
    });
  });

  if (newsSubmenu) {
    newsSubmenu.classList.toggle("is-disabled", !noiseActive);
    newsSubmenu.open = noiseActive;
  }

  validatePercentageGroups();
}

function syncSimpleToggles() {
  simpleToggles.forEach((toggle) => {
    const targetName = toggle.dataset.simpleToggle;
    const target = form.elements[targetName];
    const card = toggle.closest("[data-trader-card]");
    if (target) {
      target.disabled = !toggle.checked;
      const stepperButtons = target.parentElement?.querySelectorAll(".stepper-button") || [];
      stepperButtons.forEach((button) => {
        button.disabled = !toggle.checked;
      });
    }
    if (card) {
      card.classList.toggle("is-disabled", !toggle.checked);
    }
  });
}

numericInputs.forEach((input) => {
  const wrapper = document.createElement("div");
  const controls = document.createElement("div");
  const increaseButton = document.createElement("button");
  const decreaseButton = document.createElement("button");

  wrapper.className = "number-field";
  controls.className = "number-stepper";
  increaseButton.type = "button";
  decreaseButton.type = "button";
  increaseButton.className = "stepper-button step-up";
  decreaseButton.className = "stepper-button step-down";
  increaseButton.setAttribute("aria-label", `Aumenta ${input.name.replaceAll("_", " ")}`);
  decreaseButton.setAttribute("aria-label", `Riduci ${input.name.replaceAll("_", " ")}`);

  input.parentNode.insertBefore(wrapper, input);
  wrapper.append(input);
  controls.append(increaseButton, decreaseButton);
  wrapper.append(controls);

  input.addEventListener("input", () => {
    if (input.value.includes(",")) {
      input.value = normalizeDecimalValue(input.value);
    }
    if (input.dataset.percentGroup) {
      validatePercentageGroups();
    }
  });
  input.addEventListener("change", () => {
    clampInputValue(input);
    if (input.dataset.percentGroup) {
      validatePercentageGroups();
    }
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "ArrowUp" || event.key === "ArrowDown") {
      event.preventDefault();
      stepInput(input, event.key === "ArrowUp" ? 1 : -1);
    }
  });
  increaseButton.addEventListener("click", () => stepInput(input, 1));
  decreaseButton.addEventListener("click", () => stepInput(input, -1));
});

traderToggles.forEach((toggle) => {
  toggle.addEventListener("change", syncTraderControls);
});

simpleToggles.forEach((toggle) => {
  toggle.addEventListener("change", syncSimpleToggles);
});

async function loadDefaults() {
  resizeCanvas();
  try {
    const response = await fetch("/api/defaults");
    if (!response.ok) throw new Error("Impossibile caricare i valori di default");
    defaults = await response.json();
    fillForm(defaults);
    syncTraderControls();
    syncSimpleToggles();
    await runSimulation();
  } catch (error) {
    statusEl.textContent = descriviErrore(error);
  }
}

function fillForm(values) {
  for (const [key, value] of Object.entries(values)) {
    const input = form.elements[key];
    if (!input) continue;
    if (input.type === "checkbox") {
      input.checked = Boolean(value);
    } else {
      input.value = normalizeDecimalValue(value);
    }
  }
}

function readForm() {
  const data = {};
  for (const element of form.elements) {
    if (!element.name) continue;
    if (element.type === "checkbox") {
      data[element.name] = element.checked;
      continue;
    }
    const normalizedValue = normalizeDecimalValue(element.value);
    data[element.name] = normalizedValue === "" ? "" : Number(normalizedValue);
  }
  return data;
}

async function runSimulation() {
  const percentageValidation = validatePercentageGroups();
  if (!percentageValidation.valid) {
    statusEl.textContent = percentageValidation.messages.join(" | ");
    return;
  }

  statusEl.textContent = "Simulazione in corso";
  try {
    const response = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(readForm()),
    });

    let result;
    try {
      result = await response.json();
    } catch {
      throw new Error("Risposta del server non valida");
    }

    if (!response.ok) {
      statusEl.textContent = result.error || "Errore nella simulazione";
      return;
    }
    renderResult(result);
    statusEl.textContent = "Aggiornato";
  } catch (error) {
    statusEl.textContent = descriviErrore(error);
  }
}

function renderResult(result) {
  document.querySelector("#final-price").textContent = `$${result.summary.prezzo_finale}`;
  const changeEl = document.querySelector("#price-change");
  const variazione = result.summary.variazione_percentuale;
  changeEl.textContent = `${variazione > 0 ? "+" : ""}${variazione}%`;
  changeEl.style.color =
    variazione > 0 ? "var(--accent)" : variazione < 0 ? "var(--red)" : "var(--ink)";
  document.querySelector("#gini").textContent = result.summary.gini_finale;
  document.querySelector("#orders").textContent = `${result.summary.totale_compratori} / ${result.summary.totale_venditori}`;
  drawChart(result.giorni.map((day) => day.prezzo));
  renderPythonCharts(result.grafici);
  renderStatistiche(result.statistiche_rendimenti, result.test_adf_prezzo);
  renderPopulation(result.conteggi);
  renderTable(result.giorni.slice(-12).reverse());
}

function renderStatistiche(stat, adfPrezzo) {
  if (stat) {
    document.querySelector("#stat-media").textContent = stat.media;
    document.querySelector("#stat-dev").textContent = stat.deviazione_standard;
    document.querySelector("#stat-asimmetria").textContent = stat.asimmetria;
    document.querySelector("#stat-curtosi").textContent = stat.curtosi;
  }

  const container = document.querySelector("#adf-cards");
  if (!adfPrezzo) {
    container.innerHTML = "<p>Serie troppo corta per il test ADF (aumenta il numero di giorni).</p>";
    return;
  }

  container.innerHTML = Object.entries(adfPrezzo.valori_critici)
    .map(([livello, soglia]) => {
      const rifiuta = adfPrezzo.rifiuta_ipotesi_random_walk[livello];
      return `
        <div class="adf-card ${rifiuta ? "rifiuta" : "non-rifiuta"}">
          <span>Test ADF (prezzo) - livello ${livello}</span>
          <strong>${rifiuta ? "Rifiuta random walk" : "Non rifiuta: unit root"}</strong>
          <span>tau = ${adfPrezzo.statistica_tau} (soglia ${soglia})</span>
        </div>
      `;
    })
    .join("");
}

function renderPythonCharts(charts = {}) {
  const chartDefinitions = [
    ["patrimonio_classi", "Patrimonio classi trader"],
    ["performance_classi", "Performance e rendimento"],
    ["smart_vs_dumb", "Smart vs Normal vs Dumb"],
    ["rendimento_finale", "Rendimento finale"],
    ["istogramma_rendimenti", "Istogramma log-rendimenti (fat tail)"],
    ["acf_rendimenti", "Autocorrelazione (volatility clustering)"],
    ["gini_nel_tempo", "Gini nel tempo"],
    ["curva_lorenz", "Curva di Lorenz"],
    ["volumi_giornalieri", "Volumi giornalieri"],
    ["offerta_bitcoin", "Bitcoin in circolazione (mining)"],
    ["trader_attivi", "Trader attivi nel tempo"],
  ];

  pythonChartsEl.innerHTML = chartDefinitions
    .filter(([key]) => charts[key])
    .map(
      ([key, title]) => `
        <figure class="python-chart">
          <figcaption>${title}</figcaption>
          <img src="${charts[key]}" alt="${title}">
        </figure>
      `
    )
    .join("");
}

function drawChart(values) {
  lastPriceSeries = values;
  const width = canvas.clientWidth || 980;
  const height = canvas.clientHeight || 360;
  const padLeft = 46;
  const padRight = 16;
  const padTop = 16;
  const padBottom = 26;
  const styles = getComputedStyle(document.documentElement);
  const lineColor = styles.getPropertyValue("--line").trim() || "#1a2a26";
  const mutedColor = styles.getPropertyValue("--muted").trim() || "#8fa19b";
  const accentColor = styles.getPropertyValue("--accent").trim() || "#00c48c";
  ctx.clearRect(0, 0, width, height);

  if (!values.length) return;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 0.0001);
  const plotWidth = width - padLeft - padRight;
  const plotHeight = height - padTop - padBottom;
  const xFor = (index) => padLeft + (plotWidth * index) / Math.max(values.length - 1, 1);
  const yFor = (value) => padTop + plotHeight - ((value - min) / range) * plotHeight;

  ctx.strokeStyle = lineColor;
  ctx.lineWidth = 1;
  ctx.font = "12px system-ui, sans-serif";
  ctx.fillStyle = mutedColor;
  ctx.textAlign = "left";

  for (let i = 0; i < 5; i++) {
    const y = padTop + (plotHeight * i) / 4;
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(width - padRight, y);
    ctx.stroke();
    ctx.fillText((max - (range * i) / 4).toFixed(2), 6, y + 4);
  }

  const xTicks = Math.min(6, values.length);
  ctx.textAlign = "center";
  for (let i = 0; i < xTicks; i++) {
    const t = xTicks === 1 ? 0 : i / (xTicks - 1);
    const index = Math.round(t * (values.length - 1));
    ctx.fillText(String(index + 1), xFor(index), height - 8);
  }

  ctx.beginPath();
  values.forEach((value, index) => {
    const x = xFor(index);
    const y = yFor(value);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.strokeStyle = accentColor;
  ctx.lineWidth = 3;
  ctx.stroke();

  const lastX = xFor(values.length - 1);
  const lastY = yFor(values.at(-1));
  ctx.fillStyle = accentColor;
  ctx.beginPath();
  ctx.arc(lastX, lastY, 5, 0, Math.PI * 2);
  ctx.fill();
  ctx.textAlign = "right";
  ctx.fillText(`$${values.at(-1).toFixed(2)}`, lastX - 8, lastY - 10);
  ctx.textAlign = "left";
}

function renderPopulation(counts) {
  const total = Object.values(counts).reduce((sum, value) => sum + value, 0) || 1;
  const rows = [
    ["Random", counts.Random, ""],
    ["Noise", counts.Noise, "noise"],
    ["Chartist", counts.Chartist, "chartist"],
    ["Smart", counts.Smart, "smart"],
  ];

  document.querySelector("#population-bars").innerHTML = rows
    .map(([name, value, className]) => {
      const pct = Math.round((value / total) * 100);
      return `
        <div class="bar-row">
          <div class="bar-label"><span>${name}</span><span>${value} (${pct}%)</span></div>
          <div class="bar-track"><div class="bar-fill ${className}" style="width: ${pct}%"></div></div>
        </div>
      `;
    })
    .join("");
}

function renderTable(days) {
  document.querySelector("#days-table").innerHTML = days
    .map(
      (day) => `
        <tr>
          <td>${day.giorno}</td>
          <td>${day.notizia}</td>
          <td>$${day.prezzo}</td>
          <td>${day.compratori}</td>
          <td>${day.venditori}</td>
        </tr>
      `
    )
    .join("");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  await runSimulation();
});

resetButton.addEventListener("click", async () => {
  fillForm(defaults);
  syncTraderControls();
  syncSimpleToggles();
  await runSimulation();
});

// --- Simulazioni multiple (Monte Carlo / sensitivity) ---

const multirunButton = document.querySelector("#multirun-button");
const multirunStatus = document.querySelector("#multirun-status");
const multirunResults = document.querySelector("#multirun-results");

function normalizeOptionalNumber(value) {
  const normalized = normalizeDecimalValue(value ?? "");
  if (normalized === "") return null;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

function renderMultirun(livelli) {
  multirunResults.innerHTML = livelli
    .map((livello) => {
      const righeGruppi = Object.entries(livello.rendimento_medio_gruppi)
        .map(([nome, valore]) => `<tr><td>${nome}</td><td>${valore === null ? "-" : valore + "%"}</td></tr>`)
        .join("");
      const graficoFan = livello.grafico_fan_prezzo
        ? `<figure class="python-chart"><figcaption>Prezzo medio (banda min-max tra le run)</figcaption><img src="${livello.grafico_fan_prezzo}" alt="Prezzo medio tra le run"></figure>`
        : "";
      return `
        <article class="multirun-level">
          <h3>${livello.etichetta} — ${livello.numero_run} run, prezzo medio finale $${livello.prezzo_medio_finale ?? "-"}, win-rate Smart vs Dumb: ${livello.win_rate_smart_vs_dumb ?? "-"}%</h3>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Gruppo</th><th>Rendimento medio</th></tr></thead>
              <tbody>${righeGruppi}</tbody>
            </table>
          </div>
          <div class="chart-grid">
            ${graficoFan}
            <figure class="python-chart"><figcaption>Smart vs Dumb, ogni punto e' una run</figcaption><img src="${livello.grafico_scatter_smart_dumb}" alt="Scatter smart vs dumb"></figure>
            <figure class="python-chart"><figcaption>Differenza di rendimento (Smart - Dumb)</figcaption><img src="${livello.grafico_istogramma_differenza}" alt="Istogramma differenza smart dumb"></figure>
          </div>
        </article>
      `;
    })
    .join("");
}

async function eseguiMultirun() {
  const percentageValidation = validatePercentageGroups();
  if (!percentageValidation.valid) {
    multirunStatus.textContent = "Sistema prima i parametri a sinistra: " + percentageValidation.messages.join(" | ");
    return;
  }

  const numeroRun = normalizeOptionalNumber(document.querySelector("#multirun-numero").value) ?? 30;
  const parametro = document.querySelector("#multirun-parametro").value || null;
  const valori = [1, 2, 3]
    .map((indice) => normalizeOptionalNumber(document.querySelector(`#multirun-valore${indice}`).value))
    .filter((valore) => valore !== null);

  const payload = { ...readForm(), numero_run: numeroRun };
  if (parametro && valori.length > 0) {
    payload.parametro_confronto = parametro;
    payload.valori_confronto = valori;
  }

  multirunStatus.textContent = "Esecuzione in corso, puo' richiedere qualche secondo...";
  multirunButton.disabled = true;
  try {
    const response = await fetch("/api/multirun", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    let result;
    try {
      result = await response.json();
    } catch {
      throw new Error("Risposta del server non valida");
    }

    if (!response.ok) {
      multirunStatus.textContent = result.error || "Errore nell'esecuzione multipla";
      return;
    }
    renderMultirun(result.livelli);
    multirunStatus.textContent = "Completato";
  } catch (error) {
    multirunStatus.textContent = descriviErrore(error);
  } finally {
    multirunButton.disabled = false;
  }
}

multirunButton.addEventListener("click", eseguiMultirun);

loadDefaults();
