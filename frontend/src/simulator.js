import "./style.css";

import { simulateLoan } from "./api.js";
import { formatCurrency, formatDate, formatMonthCount, formatPercentFromDecimal } from "./format.js";

const form = document.getElementById("simulatorForm");
const amountInput = document.getElementById("amount");
const amountRange = document.getElementById("amountRange");
const toggleScheduleButton = document.getElementById("toggleSchedule");
const scheduleWrap = document.getElementById("scheduleWrap");
const statusBanner = document.getElementById("statusBanner");
const amortizationMethodInput = document.getElementById("amortizationMethod");
const interestPaymentGroup = document.getElementById("interestPaymentGroup");
const parcelaFrequencyGroup = document.getElementById("parcelaFrequencyGroup");

let scheduleExpanded = true;
let requestCounter = 0;

const output = {
  heroPrincipal: document.getElementById("heroPrincipal"),
  heroTenor: document.getElementById("heroTenor"),
  heroMode: document.getElementById("heroMode"),
  heroTotalPaid: document.getElementById("heroTotalPaid"),
  cetPa: document.getElementById("cetPa"),
  cetPm: document.getElementById("cetPm"),
  nominalPa: document.getElementById("nominalPa"),
  nominalPm: document.getElementById("nominalPm"),
  iofValue: document.getElementById("iofValue"),
  feesValue: document.getElementById("feesValue"),
  totalDebt: document.getElementById("totalDebt"),
  totalPaid: document.getElementById("totalPaid"),
  interestTotal: document.getElementById("interestTotal"),
  scheduleBody: document.getElementById("scheduleBody"),
};

function setStatus(message, tone = "neutral") {
  statusBanner.textContent = message;
  statusBanner.dataset.tone = tone;
}

function getSelectedRadioValue(name) {
  return form.querySelector(`input[name="${name}"]:checked`)?.value;
}

function buildPayload() {
  const amortizationMethod = amortizationMethodInput.value;

  return {
    amount_brl: Number(amountInput.value),
    tenor_months: Number(getSelectedRadioValue("tenor")),
    interest_payment:
      amortizationMethod === "tabela_price"
        ? "bullet"
        : getSelectedRadioValue("interest_payment"),
    parcela_frequency:
      amortizationMethod === "tabela_price"
        ? "monthly"
        : getSelectedRadioValue("parcela_frequency"),
    amortization_method: amortizationMethod,
    state: document.getElementById("state").value,
    disbursement_date: document.getElementById("disbursementDate").value,
  };
}

function syncAmountInputs(source) {
  const value = source.value;
  amountInput.value = value;
  amountRange.value = value;
}

function renderSchedule(schedule) {
  output.scheduleBody.innerHTML = "";

  schedule.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.month}</td>
      <td>${formatDate(row.date)}</td>
      <td>${formatCurrency(row.interest_accrual)}</td>
      <td>${formatCurrency(row.interest_payment)}</td>
      <td>${formatCurrency(row.principal_payment)}</td>
      <td>${formatCurrency(row.balance_eop)}</td>
      <td>${formatCurrency(row.cash_flow_to_borrower)}</td>
    `;
    output.scheduleBody.appendChild(tr);
  });
}

function renderQuote(quote) {
  output.heroPrincipal.textContent = formatCurrency(quote.principal_brl);
  output.heroTenor.textContent = formatMonthCount(quote.inputs.tenor_months);
  output.heroMode.textContent =
    quote.inputs.amortization_method === "tabela_price"
      ? "Tabela Price"
      : quote.inputs.interest_payment === "bullet"
        ? "Bullet"
        : "Coupon";
  output.heroTotalPaid.textContent = formatCurrency(quote.total_paid_brl);

  output.cetPa.textContent = formatPercentFromDecimal(quote.cet_pa);
  output.cetPm.textContent = `${formatPercentFromDecimal(quote.cet_pm)} ao mes`;
  output.nominalPa.textContent = formatPercentFromDecimal(quote.nominal_rate_pa);
  output.nominalPm.textContent = `${formatPercentFromDecimal(quote.nominal_rate_pm)} ao mes`;
  output.iofValue.textContent = formatCurrency(quote.iof_brl);
  output.feesValue.textContent = formatCurrency(quote.fees_brl);
  output.totalDebt.textContent = formatCurrency(quote.total_debt_brl);
  output.totalPaid.textContent = formatCurrency(quote.total_paid_brl);
  output.interestTotal.textContent = `Juros totais: ${formatCurrency(quote.total_interest_brl)}`;

  renderSchedule(quote.schedule);
}

async function runSimulation() {
  const currentRequest = ++requestCounter;
  setStatus("Calculando simulacao...", "loading");

  try {
    const quote = await simulateLoan(buildPayload());
    if (currentRequest !== requestCounter) {
      return;
    }
    renderQuote(quote);
    setStatus("Simulacao atualizada.", "success");
  } catch (error) {
    if (currentRequest !== requestCounter) {
      return;
    }
    setStatus(error.message, "error");
  }
}

function toggleSchedule() {
  scheduleExpanded = !scheduleExpanded;
  scheduleWrap.hidden = !scheduleExpanded;
  toggleScheduleButton.textContent = scheduleExpanded ? "Recolher tabela" : "Expandir tabela";
}

function syncAmortizationControls() {
  const isTabelaPrice = amortizationMethodInput.value === "tabela_price";

  interestPaymentGroup.hidden = isTabelaPrice;
  parcelaFrequencyGroup.hidden = isTabelaPrice;
}

amountInput.addEventListener("input", () => {
  syncAmountInputs(amountInput);
  runSimulation();
});

amountRange.addEventListener("input", () => {
  syncAmountInputs(amountRange);
  runSimulation();
});

form.addEventListener("change", () => {
  syncAmountInputs(amountInput);
  syncAmortizationControls();
  runSimulation();
});

toggleScheduleButton.addEventListener("click", toggleSchedule);

syncAmortizationControls();
runSimulation();
