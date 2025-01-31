from urllib.parse import urlunsplit, urljoin
import httpx
import logging

logger = logging.getLogger("uvicorn")


class Manager:
	def __init__(self):
		self.__client = httpx.AsyncClient()

	def setup(self, environ):
		manager_svc_host = environ["MANAGER_SERVICE_HOST"]
		manager_svc_port = environ["MANAGER_SERVICE_PORT"]
		pod_ip = environ["POD_IP"]

		self.__url = urlunsplit((
			"http",
			manager_svc_host + ":" + manager_svc_port,
			"",
			"",
			""
		))
		self.__callback = urlunsplit((
			"http",
			pod_ip + ":8000",
			"",
			"",
			""
		))

	async def register(self):
		while True:
			url = urljoin(self.__url, "register")
			logger.info("Registering at {}".format(url))

			try:
				await self.__client.post(url, json={
					'callback': self.__callback
				})
				break
			except httpx.ConnectTimeout:
				logger.info("Retrying...")
