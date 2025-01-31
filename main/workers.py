from redis import Redis
from urllib.parse import urljoin
import logging
import httpx

log = logging.getLogger("uvicorn")

class Workers:
	def __init__(self):
		self.__redis = None

	def connect(self, host, port):
		self.__redis = Redis(
			host = host,
			port = port,
			decode_responses = True
		)

	def get(self, id):
		if self.__redis is None:
			log.warn("Redis not ready")
			return None

		return self.__redis.get(id)

	def request(self, id, path):
		worker = self.get(id)

		if worker is None:
			log.warn("Redis not ready")
			raise LookupError()

		log.info("Request {}".format(urljoin(worker, path)))
		response = httpx.get(urljoin(worker, path), follow_redirects = True)
		response.raise_for_status()

		return response.json()
