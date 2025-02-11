from redis import Redis
import logging
from models import Lease
from google.cloud import storage

BUCKET_NAME = "irio-bucket-2025"
LEASE_DURATION = 60

log = logging.getLogger("uvicorn")


class Service:
    """Manages shard leases using Redis as shared storage between instances

    Each active lease is an entry where:
    * key is the shard's name
    * value is the base URL of the worker holding the lease
    * entry is set to expire after LEASE_DURATION seconds

    The entry's expiry timeout should be extended to renew an existing lease
    """

    def __init__(self):
        self.__redis = None
        self.__shards = []

    def connect(self, host, port):
        """Connect to GCS and Redis and initialize."""
        self.__gcs = storage.Client.from_service_account_json("keys.json")
        groups = self.__gcs.list_blobs(BUCKET_NAME)

        for group in groups:
            if group.name.startswith("data_"):
                self.__shards.append(group.name[5:-5])

        self.__redis = Redis(host=host, port=port, decode_responses=True)

    def __new_lease(self, shard):
        """Construct and return a new lease object."""
        return Lease(name=shard, duration=LEASE_DURATION)

    def __try_lease(self, shard, lessee):
        """Atomically try to acquire a new lease and return if successful."""
        return self.__redis.set(shard, lessee, nx=True, ex=LEASE_DURATION)

    def __try_renew(self, shard, lessee):
        """Atomically try to extend the current lease and return if successful."""
        r = self.__redis.getex(shard, ex=LEASE_DURATION)
        return r == lessee

    def lease(self, registration):
        """Handle a new lease request and return it if acquired."""
        if self.__redis is None:
            log.warning("Redis not ready")
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

        log.warning("No lease to {}".format(registration.url))
        return None
