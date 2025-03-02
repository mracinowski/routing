import jsonpickle
from fastapi import FastAPI, HTTPException
from common import fileOperations, graph
import uuid
import logging
from main.workers import Workers
import os

app = FastAPI()
logger = logging.getLogger("uvicorn")
workers = Workers()

# Does this main have authority to update the graph data for the global data?
# There can be only one main with authority.
isAuthoritative = True


class MainData:
    # Lock of the current state of the data.
    dataLock = ""
    # List of all datacenters.
    dataCenters = []
    # Map each server id to its datacenter.
    serverToDcMapping = {}
    # Count a number of external connections each server has.
    noExternalConnections = {}
    # Map each edge id to its datacenter. -1 if external.
    edgesToDC = {}
    # Maps each datacenter into its external connections.
    externalEdges: dict[str, list[graph.Edge]] = {}
    # Maps each datacenter into its passthrough connections [datacenter->(server->edges)].
    internalPassthrough: dict[str, dict[str, list[graph.Edge]]] = {}


data = MainData()
dataFile = "datam.json"
lockFile = "lockm.lock"


def refresh_data():
    """For non-authoritative workers, check if there is new data present and load."""
    logger.info("refreshData()")
    global data
    if fileOperations.check_lock(lockFile, data.dataLock):
        logger.info("refreshData(): nothing to refresh")
        return
    text_data = fileOperations.read_file(dataFile)
    data = jsonpickle.loads(text_data)
    logger.info("refreshData(): refreshed")


def save_data():
    """Save main data into the storage."""
    data.dataLock = uuid.uuid4()
    text_data = jsonpickle.encode(data)
    fileOperations.save_file(dataFile, text_data)
    fileOperations.save_file(lockFile, str(data.dataLock))


def pass_to_workers(dc_id, endpoint) -> dict:
    """Call given worker with given endpoint."""
    received_data = workers.request(dc_id, endpoint)
    if received_data["status"] != "Ok":
        raise HTTPException(500, "Internal communication error")
    return received_data


def ensure_existing_node(node):
    """Check if given node exists."""
    if node not in data.serverToDcMapping:
        raise HTTPException(400, "Invalid node ID")


def ensure_fresh_worker_data():
    """Ensure main has fresh passthrough data from each worker."""
    global data
    for dc in data.dataCenters:
        # gets current data from worker (datacenter)
        data2 = pass_to_workers(dc, "getPassthroughData/XD/")["data"]
        logger.info(data2)
        # updates the global data structure
        for i in range(len(data2["nodes"])):
            a = data2["nodes"][i]
            data.internalPassthrough[dc][a] = []
            for j in range(len(data2["nodes"])):
                b = data2["nodes"][j]
                lent = data2["matrix"][a][j]
                data.internalPassthrough[dc][a].append(
                    graph.Edge(a, b, uuid.uuid4(), lent)
                )


@app.on_event("startup")
async def startup():
    logger.info("main startup")
    workers.connect(os.environ["REDIS_SERVICE_HOST"], os.environ["REDIS_SERVICE_PORT"])
    logger.info("main connected")
    refresh_data()
    logger.info("main startup finished")


@app.get("/logs")
def get_logs():
    """Debugging endpoint - returns dump of current data."""
    return jsonpickle.dumps(data, include_properties=True)


@app.get("/getRoute/{start}/{end}")
def get_route(start: str, end: str):
    """Get the shortest path between two nodes."""
    # 1. Check correctness of the input.
    for i in [start, end]:
        ensure_existing_node(i)
    # 2. Ask getDistancesMatrix for start and end nodes.
    starting_points = pass_to_workers(
        data.serverToDcMapping[start], f"/getDistancesMatrix/{start}"
    )["data"]
    ending_points = pass_to_workers(
        data.serverToDcMapping[end], f"/getDistancesMatrix/{end}"
    )["data"]
    # 3. Find the data centers through the fastest path goes through.
    ensure_fresh_worker_data()
    edges = prepare_all_edges(starting_points, ending_points, start, end)
    res = graph.PathResult(start, end)
    graph.dijkstra(start, edges, res.callback)
    distance = res.dist
    path = res.compute()
    # 4. If it's internal connection, ask also for getInternalConnection between start and end.
    if data.serverToDcMapping[start] == data.serverToDcMapping[end]:
        internal = pass_to_workers(
            data.serverToDcMapping[start], f"/getInternalConnection/{start}/{end}/"
        )
        if internal["distance"] < distance:
            return internal
    # 5. Ask getInternalConnection for each segment.
    full_path = []
    for i in range(1, len(path)):
        if data.serverToDcMapping[path[i - 1]] == data.serverToDcMapping[path[i]]:
            part: list = pass_to_workers(
                data.serverToDcMapping[path[i]],
                f"/getInternalConnection/{path[i - 1]}/{path[i]}/",
            )["path"]
            for element in part:
                full_path.append(element)
            full_path.pop()
        else:
            full_path.append(path[i - 1])
    full_path.append(end)

    # 6. Construct answer from the pieces.
    return {"status": "Ok", "distance": distance, "path": full_path}


def prepare_all_edges(
    edge_connection1: dict[str, int], edge_connection2: dict[str, int], point1, point2
):
    """Prepares a dictionary of edges in a form required by our Dijkstra implementation."""
    logger.info("prepareAllEdges()")
    all_edges: dict[str, list[graph.Edge]] = {}
    for dc in data.internalPassthrough:
        for server in data.internalPassthrough[dc]:
            if server not in all_edges:
                all_edges[server] = []
            all_edges[server].extend(data.internalPassthrough[dc][server])
    for key in data.externalEdges:
        if key not in all_edges:
            all_edges[key] = []
        logger.warning(f"Extending by: {data.externalEdges[key]}")
        all_edges[key].extend(data.externalEdges[key])
    if point1 not in all_edges:
        all_edges[point1] = []
    for edge in edge_connection1:
        all_edges[point1].append(
            graph.Edge(point1, edge, uuid.uuid4(), edge_connection1[edge])
        )
    for edge in edge_connection2:
        all_edges[edge].append(
            graph.Edge(edge, point2, uuid.uuid4(), edge_connection2[edge])
        )

    return all_edges


@app.get("/getDistance/{start}/{end}")
def get_distance(start: str, end: str):
    """Get the shortest distance between two nodes."""
    logger.info("getDistance from {} to {}".format(start, end))
    refresh_data()
    # 1. Check correctness of the input.
    for i in [start, end]:
        ensure_existing_node(i)
    # 2. Ask getDistancesMatrix for start and end nodes.
    starting_points = pass_to_workers(
        data.serverToDcMapping[start], f"/getDistancesMatrix/{start}/"
    )["data"]
    ending_points = pass_to_workers(
        data.serverToDcMapping[end], f"/getDistancesMatrix/{end}/"
    )["data"]
    # 3. Find the data centers through the fastest path goes through.
    ensure_fresh_worker_data()
    edges = prepare_all_edges(starting_points, ending_points, start, end)
    res = graph.ResultSet1()
    graph.dijkstra(start, edges, res.callback)
    distance = res.res[end]
    # 4. If it's internal connection, ask also for getInternalConnection between start and end.
    if data.serverToDcMapping[start] == data.serverToDcMapping[end]:
        internal = pass_to_workers(
            data.serverToDcMapping[start], f"/getInternalConnection/{start}/{end}/"
        )
        distance = min(distance, internal["distance"])
    logger.info("getDistance from {} to {} -> {}".format(start, end, distance))
    return {"status": "Ok", "distance": distance}


@app.get("/addEdge/{v1}/{v2}/{distance}")
def add_edge(v1: str, v2: str, distance: int):
    """
    Adds an edge between v1 and v2 internal nodes with the given distance.
    Returns the internal id of the created path.
    """
    refresh_data()
    logger.info("addEdge/{}/{}/{}".format(v1, v2, distance))
    res = {"status": "Ok"}
    for i in [v1, v2]:
        ensure_existing_node(i)

    if data.serverToDcMapping[v1] != data.serverToDcMapping[v2]:
        # Adding edge between two different datacenters.
        if isAuthoritative is False:
            # If it's not authorised to modify data, returns error.
            # Potential alternative: call authoritative worker.
            logger.error("addEdge: this node cannot edit data")
            raise HTTPException(403, "This node cannot edit data")

        edge_uuid = uuid.uuid4()  # Creates id for new edge.
        for i in [v1, v2]:
            if i not in data.externalEdges:
                data.externalEdges[i] = []
            if data.noExternalConnections[i] == 0:
                pass_to_workers(
                    data.serverToDcMapping[i], f"/setNodeStatus/{i}/external/"
                )
            data.noExternalConnections[i] += 1

        data.externalEdges[v1].append(graph.Edge(v1, v2, edge_uuid, distance))
        data.externalEdges[v2].append(graph.Edge(v2, v1, edge_uuid, distance))
        data.edgesToDC[edge_uuid] = -1
        res["id"] = edge_uuid
    else:
        # Adding edge inside one datacenter is done by the worker responsible for it.
        worker_res = pass_to_workers(
            data.serverToDcMapping[v1], f"addEdge/{v1}/{v2}/{distance}/"
        )

        if "id" not in worker_res:
            raise HTTPException(500, "Internal processing error: lacking id")

        res["id"] = worker_res[
            "id"
        ]  # id of new edge is created by worker in its processing.
        data.edgesToDC[worker_res["id"]] = data.serverToDcMapping[v1]
    save_data()
    logger.info("addEdge/{}/{}/{} -> {}".format(v1, v2, distance, res))
    return res


@app.get("/deleteEdge/{id}/")
def delete_edge(edge_id: str):
    """Deletes edge with the given id."""
    logger.info("deleteEdge/{}".format(edge_id))
    refresh_data()
    if edge_id not in data.edgesToDC:
        raise HTTPException(400, "Invalid edge ID")

    if data.edgesToDC[edge_id] == -1:
        # It's an external edge - needs to process in both datacenters and in main.
        if isAuthoritative is False:
            # If it's not authorised to modify data, returns error.
            # Potential alternative: call authoritative worker.
            logger.error("deleteEdge: this node cannot edit data")
            raise HTTPException(403, "This node cannot edit data")

        for key in data.externalEdges:
            for element in data.externalEdges[key]:
                if element.id == edge_id:
                    data.noExternalConnections[key] -= 1
                    if data.noExternalConnections[key] == 0:
                        pass_to_workers(
                            data.edgesToDC[key], f"/setNodeStatus/{key}/internal/"
                        )
                    data.externalEdges[key].remove(element)
        save_data()
        logger.info("deleteEdge: deleted")
    else:
        # It's an internal edge - should be processed only by worker.
        logger.info("deleteEdge: pass to workers")
        pass_to_workers(data.edgesToDC[edge_id], f"deleteEdge/{edge_id}/")
