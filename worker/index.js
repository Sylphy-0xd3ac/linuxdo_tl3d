export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const offset = url.searchParams.get("offset") || "0";

    const upstream = await fetch(
      `https://linux.do/user_badges.json?badge_id=3&offset=${offset}`,
      { headers: request.headers }
    );

    const body = await upstream.text();

    return new Response(body, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  },
};
