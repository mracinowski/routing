from redis import Redis
from urllib.parse import urljoin
import logging
import httpx

log = logging.getLogger("uvicorn")


class Workers:
    def __init__(self):
        self.__redis = None

    def connect(self, host, port):
        self.__redis = Redis(host=host, port=port, decode_responses=True)

    def get(self, w_id):
        if self.__redis is None:
            log.warning("Redis not ready")
            return None

        return self.__redis.get(w_id)

    def request(self, w_id, path):
        """Sends request to worker of a given id on a given endpoint (path)."""
        worker = self.get(w_id)

        if worker is None:
            log.warning("Redis not ready")
            raise LookupError()

        log.info("Request {}".format(urljoin(worker, path)))
        response = httpx.get(urljoin(worker, path), follow_redirects=True)
        response.raise_for_status()

        return response.json()
