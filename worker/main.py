import os
from fastapi import FastAPI
from worker.manager import Manager
import httpx
import asyncio

manager = Manager()

app = FastAPI()

@app.on_event("startup")
async def startup():
	manager.setup(os.environ)
	await manager.register()

@app.get("/manager")
async def get_manager():
	return manager.__url
