from pydantic import BaseModel

class Registration(BaseModel):
	url: str
	renew: str | None = None

class Lease(BaseModel):
	name: str
	duration: int
