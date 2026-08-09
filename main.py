import os
import sys
import json
import asyncio
import threading
import webbrowser
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent_engine import GorgonaAgent
from tools import WorkspaceTools, WORKSPACE_DIR

app = FastAPI(title="Gorgona-One AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтирование рабочей области для Live Preview
os.makedirs(os.path.join(WORKSPACE_DIR, "default"), exist_ok=True)
app.mount("/preview", StaticFiles(directory=os.path.join(WORKSPACE_DIR, "default")), name="preview")

# Модели Pydantic
class GenerateRequest(BaseModel):
    prompt: str
    provider: str = "smart"
    api_key: str = None
    ollama_url: str = "http://localhost:11434"
    project_id: str = "default"

class SaveFileRequest(BaseModel):
    path: str
    content: str
    project_id: str = "default"

@app.get("/api/health")
def health():
    return {"status": "online", "system": "Gorgona-One AI Core v1.0"}

@app.get("/api/files")
def list_files(project_id: str = "default"):
    tools = WorkspaceTools(project_id=project_id)
    return {"files": tools.list_files()}

@app.get("/api/file")
def get_file(path: str, project_id: str = "default"):
    tools = WorkspaceTools(project_id=project_id)
    res = tools.read_file(path)
    if not res["success"]:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@app.post("/api/file")
def save_file(req: SaveFileRequest):
    tools = WorkspaceTools(project_id=req.project_id)
    res = tools.write_file(req.path, req.content)
    return res

@app.post("/api/open_workspace")
def open_workspace(project_id: str = "default"):
    tools = WorkspaceTools(project_id=project_id)
    if sys.platform == "win32":
        try:
            os.startfile(tools.project_dir)
        except Exception as e:
            return {"success": False, "error": str(e)}
    return {"success": True, "path": tools.project_dir}

@app.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            prompt = payload.get("prompt", "")
            image_base64 = payload.get("image_base64", None)
            provider = payload.get("provider", "smart")
            api_key = payload.get("api_key", None)
            ollama_url = payload.get("ollama_url", "http://localhost:11434")
            project_id = payload.get("project_id", "default")
            
            agent = GorgonaAgent(
                project_id=project_id,
                provider_name=provider,
                api_key=api_key,
                ollama_url=ollama_url
            )
            
            async for step in agent.execute_task_stream(prompt, image_base64=image_base64):
                await websocket.send_json(step)
                
    except WebSocketDisconnect:
        print("Client disconnected from websocket")

# Обслуживание статичности UI
if getattr(sys, 'frozen', False):
    static_dir = os.path.join(sys._MEIPASS, "static")
else:
    static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

def free_port(port=8000):
    if sys.platform == "win32":
        try:
            import subprocess
            output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
            current_pid = os.getpid()
            for line in output.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5 and "LISTENING" in parts:
                    pid = int(parts[-1])
                    if pid != current_pid and pid > 0:
                        subprocess.call(f"taskkill /F /PID {pid}", shell=True)
        except Exception:
            pass

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    import uvicorn
    free_port(8000)
    if not getattr(sys, 'frozen', False):
        threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)
