from redis import Redis
from pydantic import BaseModel
import logging
from models import Lease

LEASE_DURATION = 5

log = logging.getLogger("uvicorn")

class Service:
	def __init__(self):
		self.__redis = None
		self.__shards = [ "asmeau", "broegua", "cuswaica" ]

	def connect(self, host, port):
		self.__redis = Redis(
			host = host,
			port = port,
			decode_responses = True
		)

	def __new_lease(self, shard):
		return Lease(name = shard, duration = LEASE_DURATION)

	def __try_lease(self, shard, lessee):
		return self.__redis.set(
			shard,
			lessee,
			nx = True,
			ex = LEASE_DURATION
		)

	def __try_renew(self, shard, lessee):
		r = self.__redis.getex(
			shard,
			ex = LEASE_DURATION
		)
		return r == lessee


	def lease(self, registration):
		if self.__redis is None:
			log.warn("Redis not ready")
			return None

		if registration.renew is not None:
			shard = registration.renew
			if self.__try_renew(registration.renew, registration.url):
				log.info("Renewed {} for {}".format(shard, registration.url))
				return self.__new_lease(shard)

		for shard in self.__shards:
			if self.__try_lease(shard, registration.url):
				log.info("Lease {} to {}".format(shard, registration.url))
				return self.__new_lease(shard)

		log.warn("No lease to {}", registration.url)
		return None

