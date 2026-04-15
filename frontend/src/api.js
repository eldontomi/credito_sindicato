const LOCAL_BASE_URL = "http://127.0.0.1:8000";

function getApiBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL;
  if (configured && configured.length > 0) {
    return configured;
  }

  const { hostname, origin } = window.location;
  return hostname === "127.0.0.1" || hostname === "localhost" ? LOCAL_BASE_URL : origin;
}

export async function simulateLoan(payload) {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/simulate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let message = "Nao foi possivel calcular a simulacao.";

    try {
      const errorBody = await response.json();
      if (typeof errorBody?.detail === "string") {
        message = errorBody.detail;
      } else if (typeof errorBody?.detail?.detail === "string") {
        message = errorBody.detail.detail;
      }
    } catch {
      message = `Erro ${response.status} ao consultar a API.`;
    }

    throw new Error(message);
  }

  return response.json();
}
