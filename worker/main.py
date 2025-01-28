import os
from common import fileOperations, graph
from fastapi import FastAPI, HTTPException
from worker.manager import Manager
import httpx
import asyncio
import uuid

manager = Manager()

app = FastAPI()

# ID if of the datacenter this worker works on
datacenterId = 0
# Does this worker have authority to update the graph data for the given datacenter
# There can be only one worker with authority over each datacenter
isAuthoritative = True

class localData:
    # Lock of the current state of the data
    dataLock = ""
    
    # Preprocessed data for passthrough
    passthroughMatrix = []
    
    # List of internal nodes
    internalNodes = []
    
    # List of external node
    externalNodes = []
    
    # List of all edges
    edges: dict[str, list[graph.edge]] = {}
    
    
data = localData()


@app.on_event("startup")
async def startup():
	manager.setup(os.environ)
	await manager.register()

# For non authoritative, check if there is new data stored about the region
# If there is update, refresh in memory data
def refreshData():
	if not fileOperations.checkLock("path/To/Lock", data.dataLock):
		return
	# Load new data into memory


# Save the current state of data to the drive
def saveData():
	pass


def ensureExistingNode(node: str):
	if (node not in data.externalNodes) and (node not in data.internalNodes):
		raise HTTPException(400, "Invalid node ID")

@app.get("/getStatus")
def getStatus():
	"""
	Get some kind of id of the current state of the network
	We don't want to send the internal data, if it hasn't changed
	"""
	return data.dataLock

@app.get("/getPassthroughData/{lastId}")
def getPassthroughData(lastId: str):
	"""
	Get the data about passthrough through the datacenter in control
	If the state didn't change since last request, based on the provided id,
	It doesn't send the data, and returns appropriate message
	This will be calculated once per data update, 
	and will use preprocessed data to answer this query. 
	"""
	res = {}
	
	if lastId == getStatus():
		res['hasData'] = False
		return res
	
	res['hasData'] = True
	res['lock'] = getStatus()
	res['data'] = {}
	res['data']['matrix'] = data.passthroughMatrix
	# List of nodes in the same order as in the matrix
	res['data']['nodes'] = [] 
	return res

@app.get("/getInternalConnection/{internalNode1}/{internalNode2}")
def getInternalConnection(internalNode1: str, internalNode2: str):
	"""
	Returns distance and exact path between between two internal nodes
	"""
	ensureExistingNode(internalNode1)
	ensureExistingNode(internalNode2)

@app.get("/getDistancesMatrix/{internalNode1}")
def getDistancesMatrix(internalNode1: str):
	"""
	Returns distance from the internal node to all external connections.
	"""
	ensureExistingNode(internalNode1)
	
	res = graph.ResultSet1()
	graph.bfs(internalNode1, data.edges, res.callback)
	
	return res

# Do we need any locks in this code? 
# TBF, I don't remember how python handles parallel code ~SC

@app.put("/addEdge/{v1}/{v2}/{distance}")
def addEdge(v1: str, v2: str, distance: int):
	"""
	Adds an edge between v1 and v2 internal nodes with the given distance.
	Returns the internal id of the created path
	"""
	if isAuthoritative == False:
		raise HTTPException(403, "This node cannot edit data")
	
	# Data checks
	for i in [v1, v2]:
		ensureExistingNode(i)
	
	edgeUUID = uuid.uuid4()
	if data.edges[v1] is None:
		data.edges[v1] = []
	
	data.edges[v1].insert(graph.edge(v1, v2, edgeUUID, distance))
	data.edges[v2].insert(graph.edge(v2, v1, edgeUUID, distance))
	
	# TODO: Update preprocessed data
	
	return {'status':'Ok'}
	
@app.delete("/deleteEdge/{id}/")
def deleteEdge(id: str):
	"""
	Deletes edge with the given id
	"""
	if isAuthoritative == False:
		raise HTTPException(403, "This node cannot edit data")

@app.post("/setNodeStatus/{id}/{status}/")
def setNodeStatus(id: str, status: str):
	"""
	Mark the node as either internal or external
	"""
	if isAuthoritative == False:
		raise HTTPException(403, "This node cannot edit data")
	
	
	if status == "internal":
		newType = False
	elif status == "external":
		newType = True
	else:
		raise HTTPException(400, "New status is invalid: expected one of [internal, external]")
	
	if ((newType == False and id in data.internalNodes) or
		(newType == True and id in data.externalNodes)):
		return {'status': 'Ok', 'message': 'No data was changed'}
	
	if (newType == False and id in data.externalNodes):
		pass #TODO: Update preprocessed data
	elif (newType == True and id in data.internalNodes):
		pass #TODO: Update preprocessed data
	else:
		raise HTTPException(400, "Invalid node ID")
	
	return {'status': 'Ok'}


@app.get("/manager")
async def get_manager():
	return manager.__url
