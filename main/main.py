import jsonpickle
from fastapi import FastAPI, HTTPException
from common import fileOperations, graph
from redis import Redis
import uuid
import logging
from main.workers import Workers
import os

app = FastAPI()
logger = logging.getLogger("uvicorn")
workers = Workers()

# Does this main have authority to update the graph data for the global data
# There can be only one main with authority
isAuthoritative = True

class MainData:
    # Lock of the current state of the data
    dataLock = ""

    dataCenters = []
    
    # Map each server id to it's datacenter
    serverToDcMapping = {}
    # Count a number of external connections each server has
    noExternalConnections = {}
    # Map each edge id to its datacenter. -1 if external
    edgesToDC = {}
    
    externalEdges: dict[str, list[graph.Edge]] = {}
    
    # Maps each datacenter into it's passthrough connections
    internalPassthrough: dict[str, dict[str, list[graph.Edge]]] = {}


data = MainData()
dataFile = "datam.json"
lockFile = "lockm.lock"
test = ""

# For non-authoritative workers, check if there is new data present and load
def refreshData():
    logger.info("refreshData()")
    global data
    if fileOperations.checkLock(lockFile, data.dataLock):
        logger.info("refreshData(): nothing to refresh")
        return
    textData = fileOperations.readFile(dataFile)
    test = textData
    data = jsonpickle.loads(textData)
    logger.info("refreshData(): refreshed")

# Save main data into storage
def saveData():
    data.dataLock = uuid.uuid4()
    textData = jsonpickle.encode(data)
    fileOperations.saveFile(dataFile, textData)
    fileOperations.saveFile(lockFile, data.dataLock)

# Call given worker with given endpoint
def passToWorkers(dcId, endpoint) -> dict:
    data = workers.request(dcId, endpoint)
    if data['status'] != 'Ok':
        raise HTTPException(500, "Internal communication error")
    return data

def ensureExistingNode(node):
    if node not in data.serverToDcMapping.keys():
        raise HTTPException(400, "Invalid node ID")

# Ensure main has fresh passthrough data from each worker
def ensureFreshWorkerData():
    refreshData()

@app.on_event("startup")
async def startup():
    logger.info("main startup")
    workers.connect(
        os.environ['REDIS_SERVICE_HOST'],
        os.environ['REDIS_SERVICE_PORT']
    )
    logger.info("main connected")
    refreshData()
    logger.info("main startup finished")
 
@app.get("/logs")
def getLogs():
    return jsonpickle.dumps(data, include_properties=True)

@app.get("/logs2")
def getLogs2():
    return test

@app.get("/getRoute/{start}/{end}")
def getRoute(start: str, end: str):
    """
    Get the shortest path between two nodes
    """
    # 1. Check correctness of the input
    for i in [start, end]:
        ensureExistingNode(i)
    # 2. Ask getDistancesMatrix for start and end nodes
    startingPoints = passToWorkers(data.serverToDcMapping[start], f'/getDistancesMatrix/{start}')['data']
    endingPoints = passToWorkers(data.serverToDcMapping[end], f'/getDistancesMatrix/{end}')['data']
    # 3. Find the data centers through the fastest path goes through
    ensureFreshWorkerData()
    edges = prepareAllEdges(startingPoints, endingPoints, start, end)
    logger.warning(jsonpickle.dumps(data))
    res = graph.PathResult(start, end)
    graph.dijkstra(start, edges, res.callback)
    distance = res.dist
    path = res.compute()
    # 4. If it's internal connection, ask also for getInternalConnection between start and end
    if data.serverToDcMapping[start] == data.serverToDcMapping[end]:
        internal = passToWorkers(data.serverToDcMapping[start], f'/getInternalConnection/{start}/{end}/')
        if internal['distance'] < distance:
            return internal 
    # 5. Ask getInternalConnection for each segment
    fullPath = []
    for i in range(1, len(path)):
        if data.serverToDcMapping[path[i-1]] == data.serverToDcMapping[path[i]]:
            part: list = passToWorkers(data.serverToDcMapping[path[i]], f'/getInternalConnection/{path[i-1]}/{path[i]}/')['path']
            for element in part:
                fullPath.append(element)
            fullPath.pop()
        else:
            fullPath.append(path[i-1])
    fullPath.append(end)
    
    # 6. Construct answer from the pieces
    return {'status': 'Ok', 'distance': distance, 'path': fullPath}

def prepareAllEdges(edgeConnection1: dict[str, int], edgeConnection2: dict[str, int], point1, point2):
    logger.info("prepareAllEdges()")
    allEdges: dict[str, list[graph.Edge]] = {}
    for dc in data.internalPassthrough.keys():
        for server in data.internalPassthrough[dc].keys():
            if server not in allEdges.keys():
                allEdges[server] = []
            allEdges[server].extend(data.internalPassthrough[dc][server])
    for key in data.externalEdges.keys():
        if key not in allEdges.keys():
            allEdges[key] = []
        logger.warning(f"Extending by: {data.externalEdges[key]}")
        allEdges[server].extend(data.externalEdges[key])
    if point1 not in allEdges.keys():
        allEdges[point1] = []
    for edge in edgeConnection1.keys():
        allEdges[point1].append(graph.Edge(point1, edge, uuid.uuid4(), edgeConnection1[edge]))
    for edge in edgeConnection2.keys():
        allEdges[edge].append(graph.Edge(edge, point2, uuid.uuid4(), edgeConnection2[edge]))

    logger.info("prepared {}".format(allEdges))
    return allEdges

@app.get("/getDistance/{start}/{end}")
def getDistance(start: str, end: str):
    """
    Get the shortest distance between two nodes
    """
    logger.info("getDistance from {} to {}".format(start, end))
    refreshData()
    # 1. Check correctness of the input
    for i in [start, end]:
        ensureExistingNode(i)
    # 2. Ask getDistancesMatrix for start and end nodes
    startingPoints = passToWorkers(data.serverToDcMapping[start], f'/getDistancesMatrix/{start}/')['data']
    endingPoints = passToWorkers(data.serverToDcMapping[end], f'/getDistancesMatrix/{end}/')['data']
    # 3. Find the data centers through the fastest path goes through
    ensureFreshWorkerData()
    edges = prepareAllEdges(startingPoints, endingPoints, start, end)
    res = graph.ResultSet1()
    graph.dijkstra(start, edges, res.callback)
    distance = res.res[end]
    # 4. If it's internal connection, ask also for getInternalConnection between start and end
    if data.serverToDcMapping[start] == data.serverToDcMapping[end]:
        internal = passToWorkers(data.serverToDcMapping[start], f'/getInternalConnection/{start}/{end}/')
        distance = min(distance, internal['distance'])
    logger.info("getDistance from {} to {} -> {}".format(start, end, distance))
    return {'status': 'Ok', 'distance': distance}

@app.get("/addEdge/{v1}/{v2}/{distance}")
def addEdge(v1: str, v2: str, distance: int):
    """
    Adds an edge between v1 and v2 internal nodes with the given distance.
    Returns the internal id of the created path
    """
    refreshData()
    logger.info("addEdge/{}/{}/{}".format(v1, v2, distance))
    res = {'status': 'Ok'}
    for i in [v1, v2]:
        ensureExistingNode(i)
        
    if data.serverToDcMapping[v1] != data.serverToDcMapping[v2]:
        if isAuthoritative is False:
            # Or alternatively call authoritative worker
            logger.error("addEdge: this node cannot edit data")
            raise HTTPException(403, "This node cannot edit data")
        
        edgeUUID = uuid.uuid4()
        for i in [v1, v2]:
            if i not in data.externalEdges.keys():
                data.externalEdges[i] = []
            if data.noExternalConnections[i] == 0:
                passToWorkers(data.serverToDcMapping[i], f'/setNodeStatus/{i}/external/')
            data.noExternalConnections[i] += 1

        data.externalEdges[v1].append(graph.Edge(v1, v2, edgeUUID, distance))
        data.externalEdges[v2].append(graph.Edge(v2, v1, edgeUUID, distance))
        data.edgesToDC[edgeUUID] = -1
        res['id'] = edgeUUID
    else:
        workerRes = passToWorkers(data.serverToDcMapping[v1], f'addEdge/{v1}/{v2}/{distance}/')
        
        if 'id' not in workerRes.keys():
            raise HTTPException(500, "Internal processing error: lacking id")        
        
        res['id'] = workerRes['id']
        data.edgesToDC[workerRes['id']] = data.serverToDcMapping[v1]
    saveData()
    logger.info("addEdge/{}/{}/{} -> {}".format(v1, v2, distance, res))
    return res
    # 1. Check if this is internal of external connection
    # 2a. If internal, call appropriate worker
    # 2b. If external: ...?
    
@app.get("/deleteEdge/{id}/")
def deleteEdge(id: str):
    """
    Deletes edge with the given id
    """
    logger.info("deleteEdge/{}".format(id))
    refreshData()
    if id not in data.edgesToDC.keys():
        raise HTTPException(400, "Invalid edge ID")
    
    if data.edgesToDC[id] == -1:
        if isAuthoritative is False:
            # Or alternatively call authoritative worker
            logger.error("deleteEdge: this node cannot edit data")
            raise HTTPException(403, "This node cannot edit data")

        for key in data.externalEdges.keys():
            for element in data.externalEdges[key]:
                if element.id == id:
                    data.noExternalConnections[key] -= 1
                    if data.noExternalConnections[key] == 0:
                        passToWorkers(data.edgesToDC[key], f'/setNodeStatus/{key}/internal/')
                    data.externalEdges[key].remove(element)
        saveData()
        logger.info("deleteEdge: deleted")
    else:
        logger.info("deleteEdge: pass to workers")
        passToWorkers(data.edgesToDC[id], f'deleteEdge/{id}/')
    # 1. Check if this is internal of external connection
    # 2a. If internal, call appropriate worker
    # 2b. If external: ...?
