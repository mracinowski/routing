from redis import Redis
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

		response = httpx.post(urljoin(worker, path))
		response.raise_for_status()

		return response.json()
