from asyncio import sleep
from urllib.parse import urlunsplit, urljoin
import httpx
from httpx import HTTPError
import logging
from models import Registration, Lease
from pydantic import ValidationError

TIMEOUT = 2

log = logging.getLogger("uvicorn")


class Shard:
    async def __try_lease(self):
        """Attempt to acquire a lease and return it if successful."""
        registration = Registration(
            url=self.__pod_url,
            renew=None if self.__lease is None else self.__lease.name,
        )

        try:
            response = httpx.post(
                urljoin(self.__url, "lease"), json=registration.model_dump()
            )
            response.raise_for_status()

            return Lease.model_validate(response.json())
        except HTTPError:
            return None
        except ValidationError:
            return None

    def __init__(self, pod_host, pod_port, manager_host, manager_port):
        self.__lease = None
        self.__url = urlunsplit(("http", manager_host + ":" + manager_port, "", "", ""))
        self.__pod_url = urlunsplit(("http", pod_host + ":" + pod_port, "", "", ""))

    async def lease(self, callback):
        """Manage shard leasing, calling callback on change; Does not return."""
        while True:
            while self.__lease is None:
                self.__lease = await self.__try_lease()
                if self.__lease is None:
                    await sleep(TIMEOUT)

            current = self.__lease.name

            log.info("Acquired lease for {}".format(self.__lease))

            callback(self.__lease.name)

            while self.__lease is not None and self.__lease.name == current:
                await sleep(self.__lease.duration / 2.0)
                self.__lease = await self.__try_lease()

            log.info("Lease lost for {}".format(current))

    def lease_name(self):
        """Returns currently leased shard's name."""
        if self.__lease is None:
            return None

        return self.__lease.name
