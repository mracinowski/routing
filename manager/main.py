from fastapi import FastAPI
import logging
import os
from manager.service import Service
from models import Registration

app = FastAPI()
log = logging.getLogger("uvicorn")

service = Service()


@app.on_event("startup")
async def startup():
    service.connect(os.environ["REDIS_SERVICE_HOST"], os.environ["REDIS_SERVICE_PORT"])


@app.post("/lease")
async def lease(registration: Registration):
    """Acquire or renew a lease for any shard

    * **url**: Base URL of the requestee
    * **renew**: If set, name of the shard to renew
    """
    return service.lease(registration)
