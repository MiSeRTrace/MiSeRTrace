#!/usr/bin/python3
import psutil
import sys
import docker

dockerClient = docker.from_env()
APIClient = docker.APIClient(base_url="unix://var/run/docker.sock")

psTreeStore = []


def buildPsList(container, store: list):
    PID = APIClient.inspect_container(container.id)["State"]["Pid"]
    currentProcess = psutil.Process(PID)
    allProcesses = set(currentProcess.children(recursive=True) + [currentProcess])
    allThreads = set()
    for processPID in allProcesses:
        allThreads |= set(int(i.id) for i in processPID.threads())
    jsonElement = {
        "ID": container.id,
        "Name": container.name,
        "PID": PID,
        "PIDList": allThreads,
    }
    store.append(jsonElement)


def buildPsTree(container, store: list):
    PID = APIClient.inspect_container(container.id)["State"]["Pid"]
    currentProcess = psutil.Process(PID)
    jsonElement = {
        "ID": container.id,
        "Name": container.name,
        "PID": PID,
        "Children": [],
        "Threads": [thread.id for thread in currentProcess.threads()],
    }
    store.append(jsonElement)
    children = currentProcess.children()
    for child in children:
        recursiveBuild(child.pid, jsonElement["Children"])


def recursiveBuild(PID: int, store: list):
    currentProcess = psutil.Process(PID)
    jsonElement = {
        "PID": PID,
        "Children": [],
        "Threads": [thread.id for thread in currentProcess.threads()],
    }
    store.append(jsonElement)
    children = currentProcess.children()
    for child in children:
        recursiveBuild(child.pid, jsonElement["Children"])


for container in dockerClient.networks.get(sys.argv[1]).containers:
    buildPsList(container, psTreeStore)

processStore = []
openFiles = []

if len(sys.argv) == 3:
    matchList = sys.argv[2].split(",")
    for elem in psTreeStore:
        if len(
            list(
                filter(
                    lambda matchEntry: elem["ID"].startswith(matchEntry)
                    or matchEntry in elem["Name"],
                    matchList,
                )
            )
        ):
            for pid in elem["PIDList"]:
                print(pid, elem["Name"], elem["ID"], sep="\t")
else:
    for elem in psTreeStore:
        for pid in elem["PIDList"]:
            print(pid, elem["Name"], elem["ID"], sep="\t")
