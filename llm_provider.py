import os
import json
import httpx
from typing import Dict, Any, List, Optional

class LLMProvider:
    """
    Универсальный провайдер для работы с различными нейросетями:
    - Gemini API
    - OpenAI API (GPT-4o, GPT-3.5)
    - OpenRouter API
    - Ollama (Локальные модели: Llama3, DeepSeek, Qwen)
    - Built-in Smart Engine (Автономный генератор кода без ключей)
    """

    def __init__(self, provider: str = "smart", api_key: Optional[str] = None, ollama_url: str = "http://localhost:11434", model_name: str = "gorgona-smart"):
        self.provider = provider
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.ollama_url = ollama_url
        self.model_name = model_name
        
        if not self.model_name or self.model_name == "gorgona-smart":
            if self.provider == "openai":
                self.model_name = "gpt-4o"
            elif self.provider == "openrouter":
                self.model_name = "anthropic/claude-3.5-sonnet"
            elif self.provider == "ollama":
                self.model_name = "llama3"
            elif self.provider == "gemini":
                self.model_name = "gemini-1.5-pro"

    async def generate_response(self, system_prompt: str, user_prompt: str, tools_schema: Optional[List[Dict]] = None) -> Dict[str, Any]:
        if self.provider == "ollama":
            return await self._call_ollama(system_prompt, user_prompt)
        elif self.provider == "openai":
            return await self._call_openai(system_prompt, user_prompt, tools_schema)
        elif self.provider == "gemini":
            return await self._call_gemini(system_prompt, user_prompt)
        elif self.provider == "openrouter":
            return await self._call_openrouter(system_prompt, user_prompt, tools_schema)
        elif self.provider == "free":
            return await self._call_free_api(system_prompt, user_prompt)
        else:
            # Smart Autonomous Fallback Engine
            return self._call_smart_engine(user_prompt)

    async def _call_free_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Вызов бесплатных API (Pollinations.ai) без ключей"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                res = await client.post(
                    "https://text.pollinations.ai/",
                    json={
                        "model": "openai",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    }
                )
                if res.status_code == 200:
                    text = res.text
                    return {
                        "content": text,
                        "success": True
                    }
                return {"content": f"Free API error: {res.text}", "success": False}
            except Exception as e:
                return {"content": f"Free API Request failed: {str(e)}", "success": False}

    async def _call_ollama(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        headers = {}
        api_key = self.api_key or os.getenv("OLLAMA_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                target_model = self.model_name
                if not target_model or target_model in ["gorgona-smart", "llama3"]:
                    try:
                        tags_res = await client.get(f"{self.ollama_url.rstrip('/')}/api/tags", headers=headers, timeout=5.0)
                        if tags_res.status_code == 200:
                            models_data = tags_res.json().get("models", [])
                            if models_data:
                                target_model = models_data[0]["name"]
                    except Exception:
                        pass
                
                if not target_model or target_model == "gorgona-smart":
                    target_model = "llama3.2:1b"

                res = await client.post(
                    f"{self.ollama_url.rstrip('/')}/api/generate",
                    headers=headers,
                    json={
                        "model": target_model,
                        "prompt": f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:",
                        "stream": False
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    return {"content": data.get("response", ""), "success": True}
                return {"content": f"Ollama error: {res.status_code} - {res.text}", "success": False}
            except Exception as e:
                return {"content": f"Failed to connect to Ollama at {self.ollama_url}: {str(e)}", "success": False}

    async def _call_openai(self, system_prompt: str, user_prompt: str, tools_schema: Optional[List[Dict]] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {"content": "Error: OpenAI API Key is missing", "success": False}
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                payload = {
                    "model": self.model_name or "gpt-4o",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                }
                if tools_schema:
                    payload["tools"] = tools_schema
                    payload["tool_choice"] = "auto"
                    
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload
                )
                if res.status_code == 200:
                    data = res.json()
                    message = data["choices"][0]["message"]
                    return {
                        "content": message.get("content") or "",
                        "tool_calls": message.get("tool_calls"),
                        "success": True
                    }
                return {"content": f"OpenAI API error: {res.text}", "success": False}
            except Exception as e:
                return {"content": f"OpenAI Request failed: {str(e)}", "success": False}

    async def _call_gemini(self, system_prompt: str, user_prompt: str, tools_schema: Optional[List[Dict]] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {"content": "Error: Gemini API Key is missing", "success": False}
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name or 'gemini-1.5-pro'}:generateContent?key={self.api_key}"
                
                payload = {
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"parts": [{"text": user_prompt}]}]
                }
                
                if tools_schema:
                    # Gemini expects tools as [{"functionDeclarations": [...]}]
                    # For simplicity we'll just format it to what Gemini expects
                    payload["tools"] = [{"functionDeclarations": [t["function"] for t in tools_schema]}]
                    
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    parts = data["candidates"][0]["content"].get("parts", [])
                    text = ""
                    tool_calls = []
                    for part in parts:
                        if "text" in part:
                            text += part["text"]
                        if "functionCall" in part:
                            # Convert to OpenAI-style tool_calls for uniformity
                            fc = part["functionCall"]
                            tool_calls.append({
                                "id": "call_" + fc.get("name", "func"),
                                "function": {
                                    "name": fc["name"],
                                    "arguments": json.dumps(fc.get("args", {}))
                                }
                            })
                    return {
                        "content": text,
                        "tool_calls": tool_calls if tool_calls else None,
                        "success": True
                    }
                return {"content": f"Gemini API error: {res.text}", "success": False}
            except Exception as e:
                return {"content": f"Gemini Request failed: {str(e)}", "success": False}

    async def _call_openrouter(self, system_prompt: str, user_prompt: str, tools_schema: Optional[List[Dict]] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {"content": "Error: OpenRouter API Key is missing", "success": False}
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                payload = {
                    "model": self.model_name or "anthropic/claude-3.5-sonnet",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                }
                if tools_schema:
                    payload["tools"] = tools_schema
                    payload["tool_choice"] = "auto"
                    
                res = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload
                )
                if res.status_code == 200:
                    data = res.json()
                    message = data["choices"][0]["message"]
                    return {
                        "content": message.get("content") or "",
                        "tool_calls": message.get("tool_calls"),
                        "success": True
                    }
                return {"content": f"OpenRouter API error: {res.text}", "success": False}
            except Exception as e:
                return {"content": f"OpenRouter Request failed: {str(e)}", "success": False}

    def _call_smart_engine(self, user_prompt: str) -> Dict[str, Any]:
        """Умный автономный алгоритм генерации кода Gorgona-One"""
        prompt_lower = user_prompt.lower()
        
        # Анализ типа запроса
        title = "Gorgona AI Generated Web App"
        if "лендинг" in prompt_lower or "landing" in prompt_lower:
            title = "High-Tech Cyber Landing Page"
        elif "портфолио" in prompt_lower or "portfolio" in prompt_lower:
            title = "Developer Cyber Portfolio"
        elif "дашборд" in prompt_lower or "dashboard" in prompt_lower:
            title = "Analytics Cyber Dashboard"
        elif "магазин" in prompt_lower or "shop" in prompt_lower:
            title = "Futuristic Cyber Store"

        return {
            "content": "Gorgona-One Smart Engine generated full multi-file web app.",
            "success": True,
            "is_smart_generation": True,
            "project_type": title
        }
