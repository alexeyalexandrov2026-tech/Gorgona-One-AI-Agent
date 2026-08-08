import asyncio
import json
import websockets
import httpx
from bs4 import BeautifulSoup
import pytest

@pytest.mark.asyncio
async def test_gorgona_smart_engine_workflow():
    # 1. Start by connecting to WebSocket
    uri = "ws://localhost:8000/ws/agent"
    
    # Check if server is up
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get("http://localhost:8000/api/health")
            assert res.status_code == 200
            assert res.json()["status"] == "online"
        except Exception:
            pytest.fail("Gorgona-One server is not running on port 8000")

    # 2. Execute Web Socket Agentic Flow
    async with websockets.connect(uri) as websocket:
        payload = {
            "prompt": "Сделай дашборд аналитики с графиками, статистикой и фильтрами",
            "provider": "smart",
            "project_id": "test_env"
        }
        await websocket.send(json.dumps(payload))
        
        events_received = []
        while True:
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(msg)
                events_received.append(data)
                if data.get("step") == "completed":
                    break
            except asyncio.TimeoutError:
                break
                
        assert len(events_received) > 0, "No events received from agent"
        
        steps = [e["step"] for e in events_received]
        assert "thinking" in steps
        assert "file_created" in steps
        assert "completed" in steps

    # 3. Verify Files via API
    async with httpx.AsyncClient() as client:
        res = await client.get("http://localhost:8000/api/files?project_id=test_env")
        assert res.status_code == 200
        files = [f["path"] for f in res.json()["files"]]
        assert "index.html" in files
        assert "style.css" in files
        assert "script.js" in files
        
        # Verify HTML structure
        res = await client.get("http://localhost:8000/api/file?path=index.html&project_id=test_env")
        assert res.status_code == 200
        html_content = res.json()["content"]
        
        soup = BeautifulSoup(html_content, 'html.parser')
        assert soup.title.string == "Gorgona Neural Analytics Dashboard", "Title mismatch, parsing failed"
        
        # Verify cyber aesthetics present
        assert soup.find("div", class_="cyber-glow") is not None
        assert soup.find("div", class_="badge-status") is not None
