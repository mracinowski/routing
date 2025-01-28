from fastapi import FastAPI, Request
from pydantic import BaseModel
import logging

class Registration(BaseModel):
    callback: str

app = FastAPI()
logger = logging.getLogger("uvicorn")

@app.get("/")
async def hello():
	return "Hello world!"

@app.post("/register")
async def register(registration: Registration):
	logger.info("Register {}".format(registration.callback))
	return None

