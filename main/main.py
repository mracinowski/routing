from fastapi import FastAPI

app = FastAPI()

workerNodes = [] # IPs of workers / load balancers for each datacenter
authoritativeWorkers = [] # IPs of workers that have authority to change given data segment

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
def getRoute(start: str, end: str):
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
    # 1. Check if this is internal of external connection
    # 2a. If internal, call appropriate worker
    # 2b. If external: ...?
    
@app.delete("/deleteEdge/{id}/")
def deleteEdge(id: str):
    """
    Deletes edge with the given id
    """
    # 1. Check if this is internal of external connection
    # 2a. If internal, call appropriate worker
    # 2b. If external: ...?
