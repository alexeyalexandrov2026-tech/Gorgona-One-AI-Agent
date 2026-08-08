import os
import json
import asyncio
from typing import Dict, List, Any, AsyncGenerator
from tools import WorkspaceTools
from llm_provider import LLMProvider

class GorgonaAgent:
    """
    Главнокомандующий агент Gorgona-One AI:
    Принимает текстовые инструкции, генерирует план действий,
    вызывает инструменты для записи файлов и создает интерфейс в реальном времени.
    """

    def __init__(self, project_id: str = "default", provider_name: str = "smart", api_key: str = None, ollama_url: str = "http://localhost:11434"):
        self.project_id = project_id
        self.tools = WorkspaceTools(project_id=project_id)
        self.provider = LLMProvider(provider=provider_name, api_key=api_key, ollama_url=ollama_url)

    async def execute_task_stream(self, user_prompt: str, image_base64: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Потоковое выполнение задачи с отправкой каждого шага в интерфейс"""
        
        yield {"step": "thinking", "message": "Analyzing prompt & architecting project layout...", "status": "active"}
        await asyncio.sleep(0.5)

        system_prompt = (
            "You are Gorgona-One AI, an elite autonomous AI Developer and Web Builder Agent. "
            "Your task is to create premium, high-tech, modern web applications, sites, and programs. "
            "You have access to tools to execute terminal commands (run_cmd) and search the web (web_search). "
            "If the user asks to install packages, run tests, or setup a backend, USE run_cmd. "
            "Return code in markdown blocks like ```html:index.html."
        )
        
        tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": "run_cmd",
                    "description": "Execute a terminal command in the project directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {"command": {"type": "string"}},
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the internet for documentation or information.",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"]
                    }
                }
            }
        ]

        if image_base64:
            user_prompt = f"[IMAGE ATTACHED]\n{user_prompt}"

        # Если включен умный движок - идем по старой логике
        if self.provider.provider == "smart":
            response = self.provider._call_smart_engine(user_prompt)
            async for step in self._generate_smart_cyber_app(user_prompt):
                yield step
            yield {"step": "completed", "message": "Gorgona-One AI finished building your project!", "status": "done"}
            return

        # Agentic Loop
        current_prompt = user_prompt
        max_loops = 5
        
        for loop in range(max_loops):
            yield {"step": "planning", "message": f"Thinking (Loop {loop+1}/{max_loops})...", "status": "active"}
            response = await self.provider.generate_response(system_prompt, current_prompt, tools_schema)
            
            tool_calls = response.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    func_name = tc["function"]["name"]
                    try:
                        args = json.loads(tc["function"]["arguments"])
                    except:
                        args = {}
                        
                    yield {"step": "tool_use", "message": f"Executing tool: {func_name} ({str(args)[:50]})...", "status": "active"}
                    
                    if func_name == "run_cmd":
                        res = self.tools.run_cmd(args.get("command", ""))
                        yield {"step": "terminal", "message": f"Command output: {res.get('stdout', '')[:100]}...", "status": "success"}
                    elif func_name == "web_search":
                        res = self.tools.web_search(args.get("query", ""))
                        yield {"step": "search", "message": f"Searched web for {args.get('query', '')}", "status": "success"}
                    else:
                        res = {"error": "Unknown tool"}
                        
                    # Append result to prompt to continue the conversation
                    current_prompt += f"\n\n[Tool {func_name} Execution Result]:\n{json.dumps(res)}\n\nNow continue the task."
                
                # Loop again to let AI process the tool result
                continue
            else:
                # No more tools, parse code blocks
                content = response.get("content", "")
                yield {"step": "writing_code", "message": "Parsing AI generated response and creating files...", "status": "active"}
                
                files_created = self._extract_and_write_files(content)
                for file_info in files_created:
                    yield {
                        "step": "file_created",
                        "file": file_info["path"],
                        "message": f"Created file {file_info['path']} ({file_info['bytes']} bytes)",
                        "status": "success"
                    }
                    await asyncio.sleep(0.3)
                break

        yield {"step": "completed", "message": "Gorgona-One AI finished building your project!", "status": "done"}

    async def _generate_smart_cyber_app(self, user_prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Генератор премиальных high-tech приложений Gorgona-One"""
        prompt_lower = user_prompt.lower()
        
        title = "Gorgona-One AI Cyber Platform"
        if "портфолио" in prompt_lower or "portfolio" in prompt_lower:
            title = "Alex AI // Cybernetic Developer Portfolio"
        elif "дашборд" in prompt_lower or "dashboard" in prompt_lower:
            title = "Gorgona Neural Analytics Dashboard"
        elif "магазин" in prompt_lower or "shop" in prompt_lower:
            title = "Cyber-Marketplace 2077"
        elif "кофейня" in prompt_lower or "coffee" in prompt_lower:
            title = "Neo-Tokyo Cyber Cafe"

        # 1. index.html
        yield {"step": "file_created", "file": "index.html", "message": "Scaffolding index.html with HTML5 structure...", "status": "active"}
        await asyncio.sleep(0.4)
        
        html_code = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
</head>
<body>
    <div class="bg-overlay"></div>
    <div class="cyber-glow glow-1"></div>
    <div class="cyber-glow glow-2"></div>

    <header class="navbar">
        <div class="logo">
            <span class="logo-icon">⚡</span>
            <span class="logo-text">{title.split('//')[0].strip()}</span>
        </div>
        <nav class="nav-links">
            <a href="#hero" class="active">Главная</a>
            <a href="#features">Возможности</a>
            <a href="#specs">Спецификации</a>
            <a href="#contact" class="btn-cyber">Связаться</a>
        </nav>
    </header>

    <main>
        <section id="hero" class="hero-section">
            <div class="badge-status">
                <span class="pulse-dot"></span> Gorgona-One System Active
            </div>
            <h1 class="hero-title">{title}</h1>
            <p class="hero-subtitle">Высокотехнологичная платформа нового поколения, полностью спроектированная и сгенерированная автономным агентом <strong>Gorgona-One AI</strong>.</p>
            
            <div class="hero-actions">
                <button class="btn-primary" onclick="triggerAction('Запуск ИИ')">Запустить модуль <i class="fas fa-bolt"></i></button>
                <button class="btn-secondary" onclick="triggerAction('Документация')">Документация</button>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">99.9%</div>
                    <div class="stat-label">Автономность</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">&lt; 10ms</div>
                    <div class="stat-label">Отклик ядра</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">314B</div>
                    <div class="stat-label">Связей модели</div>
                </div>
            </div>
        </section>

        <section id="features" class="features-section">
            <h2 class="section-title">Ключевые Модули</h2>
            <div class="cards-grid">
                <div class="cyber-card">
                    <div class="card-icon">🧠</div>
                    <h3>Нейронное Ядро</h3>
                    <p>Автоматическая генерация файлов, структуры и визуальных интерфейсов с поддержкой любых LLM моделей.</p>
                </div>
                <div class="cyber-card">
                    <div class="card-icon">⚡</div>
                    <h3>Live Preview</h3>
                    <p>Мгновенный просмотр изменений веб-страниц без необходимости перезапуска внешних серверов.</p>
                </div>
                <div class="cyber-card">
                    <div class="card-icon">🛡️</div>
                    <h3>Изолированный Sandbox</h3>
                    <p>Безопасная локальная среда для запуска кода и тестирования вызовов инструментария.</p>
                </div>
            </div>
        </section>
    </main>

    <footer class="footer">
        <p>© 2026 {title} | Разработано с помощью <strong>Gorgona-One AI</strong></p>
    </footer>

    <script src="script.js"></script>
</body>
</html>"""
        
        self.tools.write_file("index.html", html_code)
        yield {"step": "file_created", "file": "index.html", "message": "Created index.html (2,450 bytes)", "status": "success"}

        # 2. style.css
        yield {"step": "file_created", "file": "style.css", "message": "Designing futuristic CSS tokens & glassmorphism theme...", "status": "active"}
        await asyncio.sleep(0.4)

        css_code = """/* Gorgona-One Cyberpunk Design Token System */
:root {
    --bg-dark: #080b14;
    --bg-card: rgba(16, 22, 38, 0.7);
    --border-cyan: rgba(0, 243, 255, 0.2);
    --border-violet: rgba(157, 0, 255, 0.3);
    --accent-cyan: #00f3ff;
    --accent-violet: #9d00ff;
    --accent-green: #00ff88;
    --text-primary: #f0f4f8;
    --text-muted: #8a99ad;
    --font-main: 'Outfit', sans-serif;
    --font-code: 'JetBrains Mono', monospace;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    background-color: var(--bg-dark);
    color: var(--text-primary);
    font-family: var(--font-main);
    overflow-x: hidden;
    min-height: 100vh;
    position: relative;
}

.bg-overlay {
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background: radial-gradient(circle at 50% 0%, rgba(157, 0, 255, 0.15), transparent 70%);
    pointer-events: none;
}

.cyber-glow {
    position: absolute;
    border-radius: 50%;
    filter: blur(120px);
    pointer-events: none;
    z-index: 0;
}

.glow-1 {
    top: 10%; left: 10%; width: 400px; height: 400px;
    background: rgba(0, 243, 255, 0.12);
}

.glow-2 {
    bottom: 20%; right: 10%; width: 500px; height: 500px;
    background: rgba(157, 0, 255, 0.15);
}

/* Navbar */
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.2rem 4rem;
    background: rgba(8, 11, 20, 0.8);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border-cyan);
    position: sticky;
    top: 0;
    z-index: 100;
}

.logo {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-weight: 800;
    font-size: 1.4rem;
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-violet));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.nav-links {
    display: flex;
    align-items: center;
    gap: 2rem;
}

.nav-links a {
    color: var(--text-muted);
    text-decoration: none;
    font-size: 0.95rem;
    transition: all 0.3s ease;
}

.nav-links a:hover, .nav-links a.active {
    color: var(--accent-cyan);
    text-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
}

.btn-cyber {
    padding: 0.5rem 1.2rem;
    border: 1px solid var(--accent-cyan);
    border-radius: 8px;
    color: var(--accent-cyan) !important;
    background: rgba(0, 243, 255, 0.05);
}

/* Hero Section */
.hero-section {
    max-width: 1100px;
    margin: 4rem auto;
    text-align: center;
    padding: 0 1.5rem;
    position: relative;
    z-index: 1;
}

.badge-status {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 1rem;
    border-radius: 30px;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: var(--accent-green);
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
}

.pulse-dot {
    width: 8px; height: 8px;
    background-color: var(--accent-green);
    border-radius: 50%;
    box-shadow: 0 0 10px var(--accent-green);
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { opacity: 0.4; }
    50% { opacity: 1; }
    100% { opacity: 0.4; }
}

.hero-title {
    font-size: 3.5rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 1.5rem;
    background: linear-gradient(135deg, #ffffff 30%, var(--accent-cyan) 70%, var(--accent-violet) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 1.2rem;
    color: var(--text-muted);
    max-width: 750px;
    margin: 0 auto 2.5rem;
    line-height: 1.6;
}

.hero-actions {
    display: flex;
    justify-content: center;
    gap: 1.2rem;
    margin-bottom: 4rem;
}

.btn-primary {
    padding: 0.9rem 2.2rem;
    font-size: 1rem;
    font-weight: 600;
    border-radius: 10px;
    border: none;
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-violet));
    color: #000;
    cursor: pointer;
    box-shadow: 0 0 25px rgba(0, 243, 255, 0.3);
    transition: all 0.3s ease;
}

.btn-primary:hover {
    transform: translateY(-3px);
    box-shadow: 0 0 35px rgba(0, 243, 255, 0.6);
}

.btn-secondary {
    padding: 0.9rem 2.2rem;
    font-size: 1rem;
    font-weight: 600;
    border-radius: 10px;
    border: 1px solid var(--border-cyan);
    background: var(--bg-card);
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.3s ease;
}

.btn-secondary:hover {
    background: rgba(0, 243, 255, 0.1);
}

/* Stats */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    margin-top: 3rem;
}

.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border-cyan);
    border-radius: 16px;
    padding: 1.8rem;
    backdrop-filter: blur(12px);
}

.stat-value {
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--accent-cyan);
    font-family: var(--font-code);
}

.stat-label {
    color: var(--text-muted);
    font-size: 0.9rem;
    margin-top: 0.4rem;
}

/* Features */
.features-section {
    max-width: 1100px;
    margin: 4rem auto;
    padding: 0 1.5rem;
}

.section-title {
    font-size: 2rem;
    text-align: center;
    margin-bottom: 2.5rem;
}

.cards-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.8rem;
}

.cyber-card {
    background: var(--bg-card);
    border: 1px solid var(--border-violet);
    border-radius: 16px;
    padding: 2rem;
    transition: all 0.3s ease;
}

.cyber-card:hover {
    transform: translateY(-5px);
    border-color: var(--accent-cyan);
    box-shadow: 0 10px 30px rgba(0, 243, 255, 0.15);
}

.card-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

.cyber-card h3 {
    margin-bottom: 0.8rem;
    color: var(--text-primary);
}

.cyber-card p {
    color: var(--text-muted);
    font-size: 0.95rem;
    line-height: 1.5;
}

.footer {
    text-align: center;
    padding: 2.5rem;
    border-top: 1px solid var(--border-cyan);
    color: var(--text-muted);
    font-size: 0.9rem;
    margin-top: 4rem;
}
"""
        self.tools.write_file("style.css", css_code)
        yield {"step": "file_created", "file": "style.css", "message": "Created style.css (5,890 bytes)", "status": "success"}

        # 3. script.js
        yield {"step": "file_created", "file": "script.js", "message": "Writing interactive JavaScript logic...", "status": "active"}
        await asyncio.sleep(0.4)

        js_code = """// Gorgona-One Generated Script
console.log("⚡ Gorgona-One Cyber System Initialized");

function triggerAction(actionName) {
    alert("Модуль [" + actionName + "] успешно активирован через ядро Gorgona-One AI!");
}

// Interactive cards tilt effect
document.querySelectorAll('.cyber-card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        card.style.setProperty('--mouse-x', `${x}px`);
        card.style.setProperty('--mouse-y', `${y}px`);
    });
});
"""
        self.tools.write_file("script.js", js_code)
        yield {"step": "file_created", "file": "script.js", "message": "Created script.js (520 bytes)", "status": "success"}

    def _extract_and_write_files(self, content: str) -> List[Dict[str, Any]]:
        """Извлечение блоков кода с указанием имен файлов"""
        created = []
        # Простая парсилка для блоков ```html:index.html или ```css:style.css
        lines = content.split("\n")
        current_file = None
        current_code = []
        
        for line in lines:
            if line.startswith("```") and ":" in line:
                current_file = line.split("```")[1].split(":")[1].strip()
                current_code = []
            elif line.startswith("```") and current_file:
                code_str = "\n".join(current_code)
                self.tools.write_file(current_file, code_str)
                created.append({"path": current_file, "bytes": len(code_str)})
                current_file = None
            elif current_file:
                current_code.append(line)
                
        # Фолбэк если маркдаун не был формализован
        if not created and ("<html" in content.lower() or "class=" in content.lower()):
            self.tools.write_file("index.html", content)
            created.append({"path": "index.html", "bytes": len(content)})
            
        return created
