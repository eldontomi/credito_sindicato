const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

const percentFormatter = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const integerFormatter = new Intl.NumberFormat("pt-BR", {
  maximumFractionDigits: 0,
});

export function formatCurrency(value) {
  return currencyFormatter.format(Number(value));
}

export function formatPercentFromDecimal(value) {
  return percentFormatter.format(Number(value));
}

export function formatMonthCount(value) {
  return `${integerFormatter.format(Number(value))} meses`;
}

export function formatDate(value) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

