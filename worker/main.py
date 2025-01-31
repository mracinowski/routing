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
    passthroughMatrix = {}
    # List of internal nodes
    internalNodes = []
    # List of external node
    externalNodes = []
    # List of all edges
    edges: dict[str, list[graph.Edge]] = {}


data = LocalData()
dataFile = None
lockFile = None


def update_data(lease_name):
    if lease_name is not None:
        global dataFile, lockFile
        dataFile = 'data_' + lease_name + '.json'
        lockFile = 'lock_' + lease_name + '.lock'
        refresh_data()


@app.on_event("startup")
async def lease():
    asyncio.create_task(shard.lease(update_data))


# For non-authoritative, check if there is new data stored about the region
# If there is update, refresh in memory data
def refresh_data():
    global data
    if fileOperations.check_lock(lockFile, data.dataLock):
        return
    text_data = fileOperations.read_file(dataFile)
    data = jsonpickle.loads(text_data)


# Save the current state of data to the drive
def save_data():
    data.dataLock = str(uuid.uuid4())
    logger.info(data)
    #  , include_properties=True
    text_data = jsonpickle.dumps(data)
    logger.info(text_data)
    fileOperations.save_file(dataFile, text_data)
    fileOperations.save_file(lockFile, data.dataLock)


def ensure_existing_node(node: str):
    if (node not in data.externalNodes) and (node not in data.internalNodes):
        raise HTTPException(400, "Invalid node ID")


def process_passthrough_data():
    data.passthroughMatrix = {}
    for node in data.externalNodes:
        result_set = graph.ResultSet1()
        graph.dijkstra(node, data.edges, result_set.callback)
        data.passthroughMatrix[node] = []
        for node2 in data.externalNodes:
            data.passthroughMatrix[node].append(result_set.res[node2])
    save_data()


@app.get("/test")
def test():
    return jsonpickle.encode(data)


@app.get("/test2")
def test():
    return dataFile


@app.get("/getStatus")
def get_status():
    """
    Get some kind of id of the current state of the network
    We don't want to send the internal data, if it hasn't changed
    """
    return {'status': 'Ok', 'data': data.dataLock}


@app.get("/getPassthroughData/{lastId}")
def get_passthrough_data(last_id: str):
    """
    Get the data about passthrough through the datacenter in control
    If the state didn't change since last request, based on the provided id,
    It doesn't send the data, and returns appropriate message
    This will be calculated once per data update,
    and will use preprocessed data to answer this query.
    """
    res = {'status': 'Ok'}

    if last_id == get_status():
        res['hasData'] = False
        return res

    res['hasData'] = True
    res['lock'] = get_status()
    res['data'] = {}
    res['data']['matrix'] = data.passthroughMatrix
    # List of nodes in the same order as in the matrix
    res['data']['nodes'] = data.externalNodes
    return res


@app.get("/getInternalConnection/{internalNode1}/{internalNode2}")
def get_internal_connection(internal_node1: str, internal_node2: str):
    """
    Returns distance and exact path between two internal nodes
    """
    ensure_existing_node(internal_node1)
    ensure_existing_node(internal_node2)

    graph_path = graph.PathResult(internal_node1, internal_node2)
    graph.dijkstra(internal_node1, data.edges, graph_path.callback)
    return {'status': 'Ok', 'distance': graph_path.dist, 'path': graph_path.compute()}


@app.get("/getDistancesMatrix/{internalNode1}")
def get_distances_matrix(internal_node1: str):
    """
    Returns distance from the internal node to all external connections.
    """
    ensure_existing_node(internal_node1)

    graph_res = graph.ResultSet1()
    graph.dijkstra(internal_node1, data.edges, graph_res.callback)

    return {'status': 'Ok', 'data': graph_res.res}


# Do we need any locks in this code?
# TBF, I don't remember how python handles parallel code ~SC


@app.get("/addEdge/{v1}/{v2}/{distance}")
def add_edge(v1: str, v2: str, distance: int):
    """
    Adds an edge between v1 and v2 internal nodes with the given distance.
    Returns the internal id of the created path
    """
    if not isAuthoritative:
        raise HTTPException(403, "This node cannot edit data")

    # Data checks
    for i in [v1, v2]:
        ensure_existing_node(i)

    edge_uuid = uuid.uuid4()
    for i in [v1, v2]:
        if data.edges[i] is None:
            data.edges[i] = []

    data.edges[v1].append(graph.Edge(v1, v2, edge_uuid, distance))
    data.edges[v2].append(graph.Edge(v2, v1, edge_uuid, distance))

    process_passthrough_data()
    return {'status': 'Ok', 'id': edge_uuid}


@app.get("/deleteEdge/{id}/")
def delete_edge(edge_id: str):
    """
    Deletes edge with the given id
    """
    if not isAuthoritative:
        raise HTTPException(403, "This node cannot edit data")

    for key in data.edges.keys():
        for element in data.edges[key]:
            if element.id == edge_id:
                data.edges[key].remove(element)

    process_passthrough_data()

    return {'status': 'Ok'}


@app.get("/setNodeStatus/{id}/{status}/")
def set_node_status(node_id: str, status: str):
    """
    Mark the node as either internal or external
    """
    if not isAuthoritative:
        raise HTTPException(403, "This node cannot edit data")

    if status == "internal":
        new_type = False
    elif status == "external":
        new_type = True
    else:
        raise HTTPException(400, "New status is invalid: expected one of [internal, external]")

    if ((new_type is False and node_id in data.internalNodes) or
        (new_type is True and node_id in data.externalNodes)):
        return {'status': 'Ok', 'message': 'No data was changed'}

    if new_type is False and node_id in data.externalNodes:
        data.externalNodes.remove(node_id)
        data.internalNodes.append(node_id)
    elif new_type is True and node_id in data.internalNodes:
        data.internalNodes.remove(node_id)
        data.externalNodes.append(node_id)
    else:
        raise HTTPException(400, "Invalid node ID")

    process_passthrough_data()
    return {'status': 'Ok'}
