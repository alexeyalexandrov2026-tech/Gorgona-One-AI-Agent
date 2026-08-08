import os
import sys
import shutil
import subprocess
from typing import Dict, List, Any
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

# Determine base directory (handles PyInstaller bundle)
if getattr(sys, 'frozen', False):
    # Desktop installation: use LocalAppData for persistent writable storage
    # C:\Users\<User>\AppData\Local\GorgonaOne\workspace
    local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    BASE_DIR = os.path.join(local_app_data, "GorgonaOne")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")

class WorkspaceTools:
    def __init__(self, project_id: str = "default"):
        self.project_dir = os.path.join(WORKSPACE_DIR, project_id)
        os.makedirs(self.project_dir, exist_ok=True)

    def write_file(self, relative_path: str, content: str) -> Dict[str, Any]:
        """Создание или перезапись файла в рабочей области проекта"""
        try:
            full_path = os.path.join(self.project_dir, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": relative_path, "bytes": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_file(self, relative_path: str) -> Dict[str, Any]:
        """Чтение файла из рабочей области"""
        try:
            full_path = os.path.join(self.project_dir, relative_path)
            if not os.path.exists(full_path):
                return {"success": False, "error": "File not found"}
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "path": relative_path, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_files(self) -> List[Dict[str, Any]]:
        """Получение дерева всех файлов проекта"""
        result = []
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.project_dir).replace("\\", "/")
                result.append({
                    "path": rel_path,
                    "size": os.path.getsize(full_path)
                })
        return result

    def run_cmd(self, command: str) -> Dict[str, Any]:
        """Выполнение терминальной команды в директории проекта"""
        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "returncode": res.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def web_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Поиск информации в интернете через DuckDuckGo"""
        if not DDGS:
            return {"success": False, "error": "duckduckgo-search not installed"}
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e)}
