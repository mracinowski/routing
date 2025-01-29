from fastapi import FastAPI, Request
from pydantic import BaseModel
import logging
import os
from manager.service import Service
from models import Registration

app = FastAPI()
log = logging.getLogger("uvicorn")

service = Service()

@app.on_event("startup")
async def startup():
	service.connect(
		os.environ['REDIS_SERVICE_HOST'],
		os.environ['REDIS_SERVICE_PORT']
	)

@app.get("/")
async def hello():
	return "Hello world!"

@app.post("/lease")
async def lease(registration: Registration):
	return service.lease(registration)
