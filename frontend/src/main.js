import "./style.css";

const currentYear = new Date().getFullYear();

document.querySelectorAll("[data-current-year]").forEach((node) => {
  node.textContent = String(currentYear);
});

