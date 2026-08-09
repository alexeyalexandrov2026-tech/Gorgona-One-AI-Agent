export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Пропускаем все статические файлы (HTML, CSS, JS) к встроенному серверу Cloudflare
    if (!url.pathname.startsWith("/api/")) {
      return env.ASSETS.fetch(request);
    }

    // Обрабатываем API чата
    if (url.pathname === "/api/chat" && request.method === "POST") {
      try {
        const body = await request.json();
        const prompt = body.prompt;
        
        // В онлайн-версии Gorgona-One перенаправляем все запросы на бесплатную сеть (Pollinations AI)
        // Так как на Cloudflare мы не можем запускать Python-код для управления файлами пользователя.
        const response = await fetch("https://text.pollinations.ai/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                model: "openai",
                messages: [
                    {
                        "role": "system", 
                        "content": "You are Gorgona-One AI, an elite autonomous AI Agent. You are running in Online Web Mode. You can answer questions, generate code snippets, and help the user. Note: you cannot execute terminal commands or write local files directly to the user's hard drive because you are running in the browser/Cloudflare."
                    },
                    {"role": "user", "content": prompt}
                ]
            })
        });

        if (response.ok) {
            const text = await response.text();
            
            // Возвращаем в том формате, который ожидает handleAgentStep() в app.js
            return new Response(JSON.stringify({
                step: "completed",
                message: text,
                status: "done"
            }), {
                headers: { "Content-Type": "application/json" }
            });
        } else {
            return new Response(JSON.stringify({
                step: "completed",
                message: "Cloudflare Free API Error: " + response.statusText,
                status: "error"
            }), {
                headers: { "Content-Type": "application/json" }
            });
        }
      } catch (err) {
        return new Response(JSON.stringify({
            step: "completed",
            message: "Cloudflare Worker Error: " + err.message,
            status: "error"
        }), {
            headers: { "Content-Type": "application/json" }
        });
      }
    }

    return new Response("Not found", { status: 404 });
  }
};
