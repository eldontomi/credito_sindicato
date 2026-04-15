export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/") || url.pathname === "/healthz") {
      const apiBaseUrl = env.API_BASE_URL;

      if (!apiBaseUrl) {
        return Response.json(
          {
            detail: "API_BASE_URL is not configured for this Worker.",
          },
          { status: 503 },
        );
      }

      const upstreamUrl = new URL(url.pathname + url.search, apiBaseUrl);
      const proxyRequest = new Request(upstreamUrl, request);

      return fetch(proxyRequest);
    }

    return env.ASSETS.fetch(request);
  },
};
