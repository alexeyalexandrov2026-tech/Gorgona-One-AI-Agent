/* =========================================================
   GORGONA ONE — Frontend Logic
   Pure UI integration. Backend untouched.
   ========================================================= */

let ws = null;
let attachedImageBase64 = null;
let terminalLog = "";
let activeFile = "index.html";

document.addEventListener("DOMContentLoaded", () => {
    initWebSocket();
    initEventListeners();
    loadSettings();
    loadTheme();
});


/* =========================================================
   WEBSOCKET — ZERO CHANGES TO PROTOCOL
   ========================================================= */

function initWebSocket() {
    let wsHost = window.location.host;
    if (!wsHost || wsHost.includes("tauri") || !wsHost.includes("8000")) {
        wsHost = "localhost:8000";
    }
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${wsHost}/ws/agent`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log("⚡ Connected to Gorgona-One Core WebSocket");
        updateStatus("Подключено");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleAgentStep(data);
    };

    ws.onclose = () => {
        console.log("WebSocket disconnected. Reconnecting in 3s...");
        updateStatus("Переподключение...");
        setTimeout(initWebSocket, 3000);
    };

    ws.onerror = () => {
        updateStatus("Ошибка подключения");
    };
}


/* =========================================================
   EVENT LISTENERS
   ========================================================= */

function initEventListeners() {
    const btnSend = document.getElementById("btn-send");
    const promptInput = document.getElementById("prompt-input");
    const btnNewChat = document.getElementById("btn-new-chat");
    const btnSettings = document.getElementById("btn-settings");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const btnSaveSettings = document.getElementById("btn-save-settings");
    const btnAttach = document.getElementById("btn-attach");
    const fileUpload = document.getElementById("file-upload");
    const modalOverlay = document.getElementById("modal-settings");
    const btnMobileMenu = document.getElementById("btn-mobile-menu");
    const sidebarOverlay = document.getElementById("sidebar-overlay");

    // Send
    btnSend.addEventListener("click", sendPrompt);

    // Textarea: Enter = send, Shift+Enter = new line
    promptInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendPrompt();
        }
    });

    // Auto-resize textarea
    promptInput.addEventListener("input", () => {
        promptInput.style.height = "auto";
        promptInput.style.height = Math.min(promptInput.scrollHeight, 200) + "px";
    });

    // New Chat
    btnNewChat.addEventListener("click", () => {
        const feed = document.getElementById("chat-feed");
        feed.innerHTML = "";

        // Restore welcome
        const welcome = document.createElement("div");
        welcome.className = "welcome system-welcome";
        welcome.id = "welcome-screen";
        welcome.innerHTML = `
            <div class="welcome-avatar">G</div>
            <h2 class="welcome-title">Gorgona One</h2>
            <p class="welcome-subtitle">Чем могу помочь сегодня?</p>
        `;
        feed.appendChild(welcome);

        const agentBox = document.getElementById("agent-box");
        agentBox.classList.add("hidden");
        document.getElementById("execution-steps").innerHTML = "";

        terminalLog = "";
        updateStatus("Ожидает ввода...");

        // Close sidebar on mobile
        closeMobileSidebar();
    });

    // Settings modal
    btnSettings.addEventListener("click", () => {
        modalOverlay.classList.remove("hidden");
    });

    btnCloseModal.addEventListener("click", () => {
        modalOverlay.classList.add("hidden");
    });

    // Close modal on overlay click
    modalOverlay.addEventListener("click", (e) => {
        if (e.target === modalOverlay) {
            modalOverlay.classList.add("hidden");
        }
    });

    // Close modal on Escape
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            modalOverlay.classList.add("hidden");
            closeMobileSidebar();
        }
    });

    btnSaveSettings.addEventListener("click", saveSettings);

    // Image upload
    if (btnAttach && fileUpload) {
        btnAttach.addEventListener("click", () => fileUpload.click());
        fileUpload.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (ev) => {
                    attachedImageBase64 = ev.target.result;
                    btnAttach.classList.add("attached");
                    btnAttach.title = "Изображение прикреплено";
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Theme toggle
    const themeSelect = document.getElementById("theme-select");
    if (themeSelect) {
        themeSelect.addEventListener("change", (e) => {
            setTheme(e.target.value);
        });
    }

    // Mobile sidebar
    if (btnMobileMenu) {
        btnMobileMenu.addEventListener("click", () => {
            document.getElementById("sidebar").classList.add("open");
            sidebarOverlay.classList.add("visible");
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener("click", closeMobileSidebar);
    }
}

function closeMobileSidebar() {
    document.getElementById("sidebar").classList.remove("open");
    document.getElementById("sidebar-overlay").classList.remove("visible");
}


/* =========================================================
   SEND MESSAGE — Same payload format, same WS contract
   ========================================================= */

function sendPrompt() {
    const input = document.getElementById("prompt-input");
    const promptText = input.value.trim();
    if (!promptText) return;

    // Hide welcome
    const welcome = document.querySelector(".system-welcome");
    if (welcome) welcome.style.display = "none";

    // Show execution steps bar
    const agentBox = document.getElementById("agent-box");
    agentBox.classList.remove("hidden");
    document.getElementById("execution-steps").innerHTML = "";

    // Remove any previous typing indicator
    const oldTyping = document.querySelector(".typing-indicator");
    if (oldTyping) oldTyping.remove();

    // Append user message
    appendChatMessage("You", promptText);

    // Build payload — EXACT SAME FORMAT as before
    const provider = document.getElementById("model-select").value;
    const payload = {
        prompt: promptText,
        image_base64: attachedImageBase64,
        provider: provider,
        api_key: localStorage.getItem(`key_${provider}`) || "",
        ollama_url: localStorage.getItem("ollama_url") || "http://localhost:11434"
    };

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(payload));
        updateStatus("Обработка запроса...");
        showTypingIndicator();
    } else {
        showError("Ошибка подключения к серверу Gorgona-One. Проверьте WebSocket.");
    }

    // Reset
    input.value = "";
    input.style.height = "auto";
    attachedImageBase64 = null;
    const btnAttach = document.getElementById("btn-attach");
    if (btnAttach) {
        btnAttach.classList.remove("attached");
        btnAttach.title = "Прикрепить файл";
        document.getElementById("file-upload").value = "";
    }
}


/* =========================================================
   RENDER MESSAGES — New DOM structure, same data
   ========================================================= */

function appendChatMessage(sender, text) {
    const feed = document.getElementById("chat-feed");
    const isUser = sender.toLowerCase() === "you" || sender.toLowerCase() === "user";

    const now = new Date();
    const timeString = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');

    if (isUser) {
        const row = document.createElement("div");
        row.className = "user-row";
        row.innerHTML = `
            <div class="user-message">
                ${escapeHtml(text)}
                <span class="message-time">${timeString}</span>
            </div>
        `;
        feed.appendChild(row);
    } else {
        // Remove typing indicator
        const typing = document.querySelector(".typing-indicator");
        if (typing) typing.remove();

        const row = document.createElement("div");
        row.className = "ai-row";
        row.innerHTML = `
            <div class="ai-avatar">G</div>
            <div class="ai-content">
                ${formatAIText(text)}
            </div>
        `;
        feed.appendChild(row);

        // Add message actions
        const actions = document.createElement("div");
        actions.className = "message-actions";
        actions.innerHTML = `
            <button class="message-action" onclick="copyMessage(this)" title="Копировать">
                <svg viewBox="0 0 24 24" fill="none">
                    <rect x="8" y="8" width="10" height="11" rx="1.5" stroke="currentColor" stroke-width="1.7" />
                    <path d="M16 8V6.5A1.5 1.5 0 0 0 14.5 5H6.5A1.5 1.5 0 0 0 5 6.5v8A1.5 1.5 0 0 0 6.5 16H8" stroke="currentColor" stroke-width="1.7" />
                </svg>
            </button>
            <button class="message-action" title="Нравится">
                <svg viewBox="0 0 24 24" fill="none">
                    <path d="M8 11v8H5v-8h3Zm0 0 3-7c.4-.8 1.5-.5 1.5.4v3.1h4.2c1.5 0 2.5 1.4 2.1 2.8l-1.3 5.2A2 2 0 0 1 15.6 17H8" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" />
                </svg>
            </button>
            <button class="message-action" title="Не нравится">
                <svg viewBox="0 0 24 24" fill="none">
                    <path d="M8 13V5h-3v8h3Zm0 0 3 7c.4.8 1.5.5 1.5-.4v-3.1h4.2c1.5 0 2.5-1.4 2.1-2.8l-1.3-5.2A2 2 0 0 0 15.6 7H8" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" />
                </svg>
            </button>
        `;
        feed.appendChild(actions);
    }

    // Scroll to bottom
    const scrollContainer = document.querySelector(".chat-scroll");
    scrollContainer.scrollTop = scrollContainer.scrollHeight;
}


/* =========================================================
   HANDLE AGENT STEPS — Same step.step / step.message format
   ========================================================= */

function handleAgentStep(step) {
    const stepsContainer = document.getElementById("execution-steps");

    if (step.message) {
        updateStatus(step.message);

        const item = document.createElement("div");
        item.className = `step-item ${step.status || ""}`;

        let icon = "⚡";
        if (step.status === "success") icon = "✓";
        if (step.step === "file_created") icon = "📁";
        if (step.step === "thinking") icon = "🧠";
        if (step.step === "planning") icon = "📋";
        if (step.step === "tool_use") icon = "🔧";
        if (step.step === "writing_code") icon = "✍️";

        item.innerHTML = `<span>${icon}</span> <span>${step.message}</span>`;
        stepsContainer.appendChild(item);
        stepsContainer.scrollTop = stepsContainer.scrollHeight;
    }

    if (step.step === "file_created") {
        // Preview-related calls — safe with null checks
        reloadPreview();
        refreshCodeViewer();
    }

    if (step.step === "terminal" || step.step === "search") {
        terminalLog += `[${new Date().toLocaleTimeString()}] ${step.step.toUpperCase()}: ${step.message}\n`;
        if (activeFile === "terminal") refreshCodeViewer();
    }

    if (step.step === "completed") {
        updateStatus("Готово!");

        // Remove typing indicator
        const typing = document.querySelector(".typing-indicator");
        if (typing) typing.remove();

        // If there's an AI response to show
        if (step.message && step.message !== "Gorgona-One AI finished building your project!") {
            appendChatMessage("Gorgona", step.message);
        } else {
            appendChatMessage("Gorgona", "Проект успешно создан! Проверьте результат.");
        }

        reloadPreview();
        refreshCodeViewer();

        // Auto-hide steps bar after delay
        setTimeout(() => {
            const agentBox = document.getElementById("agent-box");
            // Don't hide — keep visible for user review
        }, 2000);
    }
}


/* =========================================================
   PREVIEW & CODE VIEWER — Preserved with null-safety
   ========================================================= */

function reloadPreview() {
    const iframe = document.getElementById("preview-iframe");
    if (iframe) {
        iframe.src = `/preview/index.html?t=${Date.now()}`;
    }
}

async function refreshCodeViewer() {
    const editor = document.getElementById("code-editor");
    if (!editor) return;

    if (activeFile === "terminal") {
        editor.value = terminalLog || "// Терминал пуст. Ожидание вывода команд...";
        return;
    }
    try {
        const res = await fetch(`/api/file?path=${activeFile}`);
        if (res.ok) {
            const data = await res.json();
            editor.value = data.content;
        } else {
            editor.value = `// Файл ${activeFile} пока еще не создан...`;
        }
    } catch (e) {
        editor.value = `// Ошибка загрузки файла ${activeFile}`;
    }
}


/* =========================================================
   SETTINGS — Same localStorage keys
   ========================================================= */

function saveSettings() {
    localStorage.setItem("key_gemini", document.getElementById("input-gemini-key").value);
    localStorage.setItem("key_openai", document.getElementById("input-openai-key").value);
    localStorage.setItem("key_openrouter", document.getElementById("input-openrouter-key").value);
    localStorage.setItem("key_ollama", document.getElementById("input-ollama-key").value);
    localStorage.setItem("ollama_url", document.getElementById("input-ollama-url").value);

    document.getElementById("modal-settings").classList.add("hidden");
    showToast("Настройки API сохранены");
}

function loadSettings() {
    const geminiKey = localStorage.getItem("key_gemini");
    const openaiKey = localStorage.getItem("key_openai");
    const openrouterKey = localStorage.getItem("key_openrouter");
    const ollamaKey = localStorage.getItem("key_ollama");
    const ollamaUrl = localStorage.getItem("ollama_url");

    if (geminiKey) document.getElementById("input-gemini-key").value = geminiKey;
    if (openaiKey) document.getElementById("input-openai-key").value = openaiKey;
    if (openrouterKey) document.getElementById("input-openrouter-key").value = openrouterKey;
    if (ollamaKey) document.getElementById("input-ollama-key").value = ollamaKey;
    if (ollamaUrl) document.getElementById("input-ollama-url").value = ollamaUrl;
}


/* =========================================================
   HELPERS
   ========================================================= */

function updateStatus(text) {
    const el = document.getElementById("agent-status-text");
    if (el) el.innerText = text;
}

function showToast(message) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.remove("hidden");
    toast.classList.add("visible");
    setTimeout(() => {
        toast.classList.remove("visible");
        setTimeout(() => toast.classList.add("hidden"), 300);
    }, 2500);
}

function showError(message) {
    const feed = document.getElementById("chat-feed");
    const errorDiv = document.createElement("div");
    errorDiv.className = "error-message";
    errorDiv.textContent = message;
    feed.appendChild(errorDiv);

    const scrollContainer = document.querySelector(".chat-scroll");
    scrollContainer.scrollTop = scrollContainer.scrollHeight;
}

function showTypingIndicator() {
    const feed = document.getElementById("chat-feed");
    const typing = document.createElement("div");
    typing.className = "typing-indicator";
    typing.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    feed.appendChild(typing);

    const scrollContainer = document.querySelector(".chat-scroll");
    scrollContainer.scrollTop = scrollContainer.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, "<br>");
}

function formatAIText(text) {
    // Simple markdown-like formatting
    let html = text;

    // Code blocks
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code>${escapeHtmlRaw(code.trim())}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Wrap in paragraphs if not already structured
    if (!html.includes("<p>") && !html.includes("<pre>")) {
        html = html.split(/\n\n+/).map(p => `<p>${p.replace(/\n/g, "<br>")}</p>`).join("");
    }

    return html;
}

function escapeHtmlRaw(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function copyMessage(btn) {
    const aiContent = btn.closest(".message-actions").previousElementSibling;
    const content = aiContent ? aiContent.querySelector(".ai-content") : null;
    if (content) {
        navigator.clipboard.writeText(content.innerText).then(() => {
            showToast("Скопировано в буфер обмена");
        });
    }
}


/* =========================================================
   THEME — localStorage persistence, CSS-only switching
   ========================================================= */

function loadTheme() {
    const saved = localStorage.getItem("gorgona_theme") || "russian";
    setTheme(saved, false);

    const themeSelect = document.getElementById("theme-select");
    if (themeSelect) {
        themeSelect.value = saved;
    }
}

function setTheme(theme, notify = true) {
    if (theme === "default") {
        document.body.removeAttribute("data-theme");
    } else {
        document.body.setAttribute("data-theme", theme);
    }
    localStorage.setItem("gorgona_theme", theme);

    if (notify) {
        const label = theme === "russian" ? "Russian Blue/Red" : "Default";
        showToast(`Тема: ${label}`);
    }
}
