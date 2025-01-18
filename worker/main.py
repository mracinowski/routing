from fastapi import FastAPI
from common import fileOperations

app = FastAPI()

# ID if of the datacenter this worker works on
datacenterId = 0
# Does this worker have authority to update the graph data for the given datacenter
# There can be only one worker with authority over each datacenter
isAuthoritative = True


data = []
dataLock = ""

# For non authoritative, check if there is new data stored about the region
# If there is update, refresh in memory data
def refreshData():
    if not fileOperations.checkLock("path/To/Lock", dataLock):
        return
    # Load new data into memory

@app.get("/getStatus")
def getStatus():
    """
    Get some kind of id of the current state of the network
    We don't want to send the internal data, if it hasn't changed
    """
    return "Hello world!"

@app.get("/getPassthroughData/{lastId}")
def getPassthroughData(lastId: str):
    """
    Get the data about passthrough through the datacenter in control
    If the state didn't change since last request, based on the provided id,
    It doesn't send the data, and returns appropriate message
    """
    res = {}
    
    if lastId == getStatus():
        res['hasData'] = False
        return res
    
    res['hasData'] = True

@app.get("/getInternalConnection/{internalNode1}/{internalNode2}")
def getInternalConnection(internalNode1: str, internalNode2: str):
    """
    Returns distance and exact path between between two internal nodes
    """

@app.get("/getDistancesMatrix/{internalNode1}")
def getDistancesMatrix(internalNode1: str):
    """
    Returns distance from the internal node to all external connections.
    This will be calculated once per data update, 
    and will use preprocessed data to answer this query. 
    """

@app.put("/addEdge/{v1}/{v2}/{distance}")
def addEdge(v1: str, v2: str, distance: int):
    """
    Adds an edge between v1 and v2 internal nodes with the given distance.
    Returns the internal id of the created path
    """
    
@app.delete("/deleteEdge/{id}/")
def deleteEdge(id: str):
    """
    Deletes edge with the given id
    """
