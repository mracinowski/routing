from redis import Redis
import logging

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

