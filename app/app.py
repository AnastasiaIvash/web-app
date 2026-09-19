import os
import socket
from fastapi import FastAPI, Request, HTTPException
import redis.asyncio as redis

app = FastAPI(title="Backend Service Artifact")

# 1. Ограничение 1: Идентификация ноды (из environment или hostname)
NODE_ID = os.getenv("NODE_ID", socket.gethostname())

# 2. Ограничение 2 & 4: Внешнее хранилище сессий/данных (Redis)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


@app.get("/")
async def root():
    """Эндпоинт, однозначно идентифицирующий backend-ноду."""
    return {
        "status": "active",
        "node_id": NODE_ID,
        "message": f"Request served by backend node: {NODE_ID}"
    }


@app.get("/api/info")
async def get_node_info(request: Request):
    """Сведения о хосте и проброшенных заголовках от реверс-прокси."""
    return {
        "served_by_node": NODE_ID,
        "client_ip": request.client.host,
        "headers": dict(request.headers)
    }


@app.post("/api/session/set")
async def set_session(key: str, value: str):
    """Запись данных во внешнюю распределенную БД/Кэш."""
    try:
        await redis_client.set(key, value)
        return {"status": "success", "node": NODE_ID, "key": key, "value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")


@app.get("/api/session/get/{key}")
async def get_session(key: str):
    """Чтение данных из внешнего хранилища (доступно с любой ноды)."""
    try:
        val = await redis_client.get(key)
        if val is None:
            raise HTTPException(status_code=404, detail="Key not found")
        return {"served_by_node": NODE_ID, "key": key, "value": val}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")