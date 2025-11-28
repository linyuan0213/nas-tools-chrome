"""NAS Tools Chrome Server 入口点"""
import uvicorn
from src.main import app

if __name__ == "__main__":
    from src.config.settings import APP_HOST, APP_PORT
    
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=False)
