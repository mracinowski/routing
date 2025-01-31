import os
from common import fileOperations, graph
from fastapi import FastAPI, HTTPException
import jsonpickle
from worker.shard import Shard
import uuid
import logging
import asyncio

shard = Shard(
	os.environ["POD_HOST"],
	os.environ["POD_PORT"],
	os.environ["MANAGER_SERVICE_HOST"],
	os.environ["MANAGER_SERVICE_PORT"],
)

app = FastAPI()
log = logging.getLogger("uvicorn")
logger = logging.getLogger("uvicorn")

# ID if of the datacenter this worker works on
datacenterId = 0
# Does this worker have authority to update the graph data for the given datacenter
# There can be only one worker with authority over each datacenter
isAuthoritative = True


class LocalData:
	# Lock of the current state of the data
	dataLock = ""
	# Preprocessed data for passthrough
	passthroughMatrix = []
	# List of internal nodes
	internalNodes = []
	# List of external node
	externalNodes = []
	# List of all edges
	edges: dict[str, list[graph.Edge]] = {}


data = LocalData()
dataFile = None
lockFile = None

def updateData(lease_name):
	if lease_name is not None:
		global dataFile, lockFile
		dataFile = 'data_' + lease_name + '.json'
		lockFile = 'lock_' + lease_name + '.lock'
		refreshData()

@app.on_event("startup")
async def lease():
	asyncio.create_task(shard.lease(updateData))

# For non-authoritative, check if there is new data stored about the region
# If there is update, refresh in memory data
def refreshData():
	global data
	if fileOperations.checkLock(lockFile, data.dataLock):
		return
	textData = fileOperations.readFile(dataFile)
	data = jsonpickle.loads(textData)


# Save the current state of data to the drive
def saveData():
	data.dataLock = str(uuid.uuid4())
	logger.info(data)
#  , include_properties=True
	textData = jsonpickle.dumps(data)
	logger.info(textData)
	fileOperations.saveFile(dataFile, textData)
	fileOperations.saveFile(lockFile, data.dataLock)


def ensureExistingNode(node: str):
	if (node not in data.externalNodes) and (node not in data.internalNodes):
		raise HTTPException(400, "Invalid node ID")

def processPassthroughData():
	data.passthroughMatrix = []
	for node in data.externalNodes:
		resultSet = graph.ResultSet1()
		graph.dijkstra(node, data.edges, resultSet.callback)
		data.passthroughMatrix[node] = []
		for node2 in data.externalNodes:
			data.passthroughMatrix.append(resultSet.res[node2])
	saveData()

@app.get("/test")
def test():
    return jsonpickle.encode(data)

@app.get("/test2")
def test():
    return dataFile

@app.get("/getStatus")
def getStatus():
	"""
	Get some kind of id of the current state of the network
	We don't want to send the internal data, if it hasn't changed
	"""
	return {'status': 'Ok', 'data': data.dataLock}

@app.get("/getPassthroughData/{lastId}")
def getPassthroughData(lastId: str):
	"""
	Get the data about passthrough through the datacenter in control
	If the state didn't change since last request, based on the provided id,
	It doesn't send the data, and returns appropriate message
	This will be calculated once per data update, 
	and will use preprocessed data to answer this query. 
	"""
	res = {'status': 'Ok'}

	if lastId == getStatus():
		res['hasData'] = False
		return res

	res['hasData'] = True
	res['lock'] = getStatus()
	res['data'] = {}
	res['data']['matrix'] = data.passthroughMatrix
	# List of nodes in the same order as in the matrix
	res['data']['nodes'] = data.externalNodes
	return res

@app.get("/getInternalConnection/{internalNode1}/{internalNode2}")
def getInternalConnection(internalNode1: str, internalNode2: str):
	"""
	Returns distance and exact path between two internal nodes
	"""
	ensureExistingNode(internalNode1)
	ensureExistingNode(internalNode2)

	graphPath = graph.PathResult(internalNode1, internalNode2)
	graph.dijkstra(internalNode1, data.edges, graphPath.callback)
	return {'status': 'Ok', 'distance': graphPath.dist, 'path': graphPath.compute()}

@app.get("/getDistancesMatrix/{internalNode1}")
def getDistancesMatrix(internalNode1: str):
	"""
	Returns distance from the internal node to all external connections.
	"""
	ensureExistingNode(internalNode1)

	graphRes = graph.ResultSet1()
	graph.dijkstra(internalNode1, data.edges, graphRes.callback)

	return {'status': 'Ok', 'data': graphRes.res}

# Do we need any locks in this code?
# TBF, I don't remember how python handles parallel code ~SC

@app.get("/addEdge/{v1}/{v2}/{distance}")
def addEdge(v1: str, v2: str, distance: int):
	"""
	Adds an edge between v1 and v2 internal nodes with the given distance.
	Returns the internal id of the created path
	"""
	if not isAuthoritative:
		raise HTTPException(403, "This node cannot edit data")

	# Data checks
	for i in [v1, v2]:
		ensureExistingNode(i)

	edgeUUID = uuid.uuid4()
	for i in [v1, v2]:
		if data.edges[i] is None:
			data.edges[i] = []

	data.edges[v1].append(graph.Edge(v1, v2, edgeUUID, distance))
	data.edges[v2].append(graph.Edge(v2, v1, edgeUUID, distance))

	processPassthroughData()
	return {'status': 'Ok', 'id': edgeUUID}

@app.get("/deleteEdge/{id}/")
def deleteEdge(id: str):
	"""
	Deletes edge with the given id
	"""
	if not isAuthoritative:
		raise HTTPException(403, "This node cannot edit data")

	for key in data.edges.keys():
		for element in data.edges[key]:
			if element.id == id:
				data.edges[key].remove(element)

	processPassthroughData()

	return {'status': 'Ok'}

@app.get("/setNodeStatus/{id}/{status}/")
def setNodeStatus(id: str, status: str):
	"""
	Mark the node as either internal or external
	"""
	if not isAuthoritative:
		raise HTTPException(403, "This node cannot edit data")

	if status == "internal":
		newType = False
	elif status == "external":
		newType = True
	else:
		raise HTTPException(400, "New status is invalid: expected one of [internal, external]")

	if ((newType is False and id in data.internalNodes) or
		(newType is True and id in data.externalNodes)):
		return {'status': 'Ok', 'message': 'No data was changed'}

	if newType is False and id in data.externalNodes:
		data.externalNodes.remove(id)
		data.internalNodes.append(id)
	elif newType is True and id in data.internalNodes:
		data.internalNodes.remove(id)
		data.externalNodes.append(id)
	else:
		raise HTTPException(400, "Invalid node ID")

	processPassthroughData()
	return {'status': 'Ok'}
