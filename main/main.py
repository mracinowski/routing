from fastapi import FastAPI, HTTPException
from common import fileOperations, graph
import uuid

app = FastAPI()

workerNodes = [] # IPs of workers / load balancers for each datacenter
authoritativeWorkers = [] # IPs of workers that have authority to change given data segment

# Does this main have authority to update the graph data for the global data
# There can be only one main with authority
isAuthoritative = True

class MainData:
    # Lock of the current state of the data
    dataLock = ""

    dataCenters = []
    
    # Map each server id to it's datacenter
    serverToDcMapping = {}
    # Map each edge id to it's datacenter. -1 if external
    edgesToDC = {}
    
    externalEdges: dict[str, list[graph.edge]] = {}
    
    # Maps each datacenter into it's passthrough connections
    internalPassthrough: dict[str, dict[str, list[graph.edge]]] = {}
    
data = MainData()
    
def refreshData():
    pass

def saveData():
    pass

def passToWorkers(dcId, endpoint) -> dict:
    pass


@app.get("/getRoute/{start}/{end}")
def getRoute(start: str, end: str):
    """
    Get the shortest path between two nodes
    """
    # 1. Check correctness of the input
    # 2. Ask getDistancesMatrix for start and end nodes
    # 3. Find the data centers through the fastest path goes through
    # 4. Ask getInternalConnection for each segment
    # 5. If it's internal connection, ask also for getInternalConnection between start and end
    # 6. Construct answer from the pieces
    return "Hello world!"

@app.get("/getDistance/{start}/{end}")
def getDistance(start: str, end: str):
    """
    Get the shortest distance between two nodes
    """
    # 1. Check correctness of the input
    # 2. Ask getDistancesMatrix for start and end nodes
    # 3. Find the data centers through the fastest path goes through
    # 4. Ask getInternalConnection for each segment
    # 5. If it's internal connection, ask also for getInternalConnection between start and end
    # 6. Construct answer from the pieces
    return "Hello world!"

@app.put("/addEdge/{v1}/{v2}/{distance}")
def addEdge(v1: str, v2: str, distance: int):
    """
    Adds an edge between v1 and v2 internal nodes with the given distance.
    Returns the internal id of the created path
    """
    res = {'status': 'Kk'}
    for i in [v1, v2]:
        if i not in data.serverToDcMapping.keys():
            raise HTTPException(400, "Invalid node ID")
        
    if data.serverToDcMapping[v1] != data.serverToDcMapping[v2]:
        if isAuthoritative == False:
            # Or alternatively call authoritative worker
            raise HTTPException(403, "This node cannot edit data")        
        
        edgeUUID = uuid.uuid4()
        for i in [v1, v2]:
            if data.externalEdges[i] is None:
                data.externalEdges[i] = []
	
        data.externalEdges[v1].insert(graph.edge(v1, v2, edgeUUID, distance))
        data.externalEdges[v2].insert(graph.edge(v2, v1, edgeUUID, distance))
        data.edgesToDC[edgeUUID] = -1
        res['id'] = edgeUUID
    else:
        workerRes = passToWorkers(data.serverToDcMapping[v1], f'addEdge/{v1}/{v2}/{distance}/')
        
        if 'id' not in workerRes.keys():
            raise HTTPException(500, "Internal processing error: lacking id")        
        
        res['id'] = workerRes['id']
        data.edgesToDC[workerRes['id']] = data.serverToDcMapping[v1]
    saveData()
    return res
    # 1. Check if this is internal of external connection
    # 2a. If internal, call appropriate worker
    # 2b. If external: ...?
    
@app.delete("/deleteEdge/{id}/")
def deleteEdge(id: str):
    """
    Deletes edge with the given id
    """
    if id not in data.edgesToDC.keys():
        raise HTTPException(400, "Invalid edge ID")
    
    if data.edgesToDC[id] == -1:
        if isAuthoritative == False:
            # Or alternatively call authoritative worker
            raise HTTPException(403, "This node cannot edit data")

        for key in data.externalEdges.keys():
            for element in data.externalEdges[key]:
                if element.id == id:
                    data.externalEdges[key].remove(element)
        saveData()
    else:
        passToWorkers(data.edgesToDC[id], f'deleteEdge/{id}/')
    # 1. Check if this is internal of external connection
    # 2a. If internal, call appropriate worker
    # 2b. If external: ...?
