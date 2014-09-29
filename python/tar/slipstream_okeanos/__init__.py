from kamaki.clients.astakos import AstakosClient
from kamaki.clients.cyclades import CycladesClient
import time
import socket


class GetIP(object):
    __MyIP = None

    # noinspection PyMethodMayBeStatic
    def MyIP(self):
        if GetIP.__MyIP is None:
            # http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
            GetIP.__MyIP = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
        return GetIP.__MyIP

MyIP = GetIP()


# noinspection PyBroadException
def myHostnameAndIP():
    try:
        raise Exception()
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        betterIP = MyIP.MyIP()
        if ip == betterIP:
            return hostname, ip
        else:
            return hostname, "%s %s" % (betterIP, ip)
    except:
        return "__localhost__", "127.0.0.1"


def LOG(s):
    hostname, ip = myHostnameAndIP()
    from sys import stderr
    print >> stderr, "[~ %s %s] %s" % (hostname, ip, s)
    stderr.flush()


def LOGException(e, prefix=""):
    """
    :type e: exceptions.Exception
    """
    LOG("%sException '%s' with args %s" % (prefix, e.__class__.__name__, e.args))


def LOGSshException(username, hostname, e, prefix=">> "):
    """
    :type username: str
    :type hostname: str
    :type e: exceptions.Exception
    """
    LOG("%sException: For %s@%s got '%s' with args %s" % (prefix, username, hostname, e.__class__.__name__, e.args))


def loadRsaPrivKey(name="id_rsa"):
    """
    :type name: str
    """
    import os.path as ospath
    from paramiko.rsakey import RSAKey
    filename = ospath.expanduser("~/.ssh/%s" % name)
    LOG("Loading SSH private key from %s" % filename)
    rsaKey = RSAKey(filename=filename)
    return rsaKey


def loadPubRsaKeyData(name="id_rsa.pub"):
    """
    :type name: str
    """
    import os.path as ospath
    filename = ospath.expanduser("~/.ssh/%s" % name)
    LOG("Loading SSH public key from %s" % filename)
    with open(filename, 'r') as f:
        return f.read()


def newSshClient(hostname, username="root", localPrivKey=None, timeout=None):
    from paramiko.client import SSHClient, AutoAddPolicy

    localPrivKey = localPrivKey or loadRsaPrivKey()

    missingHostKeyPolicy = AutoAddPolicy()
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(missingHostKeyPolicy)
    ssh.connect(hostname, username=username, pkey=localPrivKey, timeout=timeout)

    return ssh


class NodeStatus(object):
    ACTIVE = 'ACTIVE'  # running
    STOPPED = 'STOPPED'  # shut down
    BUILD = 'BUILD'  # building
    DELETED = 'DELETED'
    UNKNOWN = 'UNKNOWN'

    def __init__(self, okeanosStatus):
        """
        :type okeanosStatus: str
        """
        self.okeanosStatus = okeanosStatus  # This is a string
        if okeanosStatus == NodeStatus.ACTIVE:
            self.slipstreamStatus = 'Running'  # or 'Active' or 'On'
        elif okeanosStatus == NodeStatus.STOPPED:
            self.slipstreamStatus = 'Stopped'
        elif okeanosStatus == NodeStatus.BUILD:
            self.slipstreamStatus = 'Pending'
        elif okeanosStatus == NodeStatus.DELETED:
            self.slipstreamStatus = 'Terminated'
        else:
            self.slipstreamStatus = 'Unknown'

    def __str__(self):
        return self.slipstreamStatus

    def isRunning(self):
        return self.okeanosStatus == NodeStatus.ACTIVE

    def isStopped(self):
        return self.okeanosStatus == NodeStatus.STOPPED

    def isPending(self):
        return self.okeanosStatus == NodeStatus.BUILD

    def isDeleted(self):
        return self.okeanosStatus == NodeStatus.DELETED


class ListNodeResult(object):
    def __init__(self, id, status, serverDetails):
        """
        :type serverDetails: dict
        :type status: NodeStatus
        :type id: str
        """
        self.originalInfo = serverDetails
        self.id = id
        self.status = status


class NodeDetails(object):
    def __init__(self, resultDict, sshPubKey=None, initScriptPath=None, initScriptData=None, asyncInitScriptPath=None):
        """
        :type resultDict: dict
        """
        self.sshPubKey = sshPubKey
        self.initScriptPath = initScriptPath
        self.initScriptData = initScriptData
        self.asyncInitScriptPath = asyncInitScriptPath
        self.uuid = resultDict[u'user_id']
        self.id = str(resultDict[u'id'])
        self.name = resultDict[u'name']
        okeanosStatus = resultDict[u'status']
        self.status = NodeStatus(okeanosStatus)
        self.flavorId = resultDict[u'flavor'][u'id']
        self.imageId = resultDict[u'image'][u'id']
        self.securityGroups = [ sg[u'name'] for sg in resultDict[u'security_groups'] ]
        self.suspended = resultDict[u'suspended']
        self.deleted = resultDict[u'deleted']
        self.adminPass = resultDict[u'adminPass'] if u'adminPass' in resultDict else None
        self.tenantId = resultDict[u'tenant_id']
        self.snfTaskState = resultDict[u'SNF:task_state']  # BUILDING
        self.snfFQDN = resultDict[u'SNF:fqdn']
        ipv4s = []
        ipv6s = []
        if u'addresses' in resultDict:
            addressesRaw = resultDict[u'addresses']
            for key in addressesRaw:
                for item in addressesRaw[key]:
                    version = item[u'version']
                    address = item[u'addr']
                    if version in [4, '4']:
                        ipv4s.append(address)
                    elif version in [6, '6']:
                        ipv6s.append(address)
        self.ipv4s = ipv4s
        self.ipv6s = ipv6s

    def updateStatusFrom(self, that):
        """
        :type that: NodeDetails
        """
        self.status = that.status
        self.snfTaskState = that.snfTaskState
        self.deleted = that.deleted
        self.suspended = that.suspended

    def updateIPsFrom(self, that):
        """
        :type that: NodeDetails
        """
        if that.ipv4s:
            self.ipv4s = that.ipv4s
        if that.ipv6s:
            self.ipv6s = that.ipv6s

    def updateIPsAndStatusFrom(self, that):
        """
        :type that: NodeDetails
        """
        self.updateStatusFrom(that)
        self.updateIPsFrom(that)


def runCommandOnHost(hostname, command,
                     username='root',
                     localPrivKey=None,
                     timeout=None,
                     runSynchronously=True):
    """
    :type timeout: int
    :type localPrivKey: str
    :type hostname: strs
    :type command: str
    """

    if not runSynchronously:
        command = "at -f %s now" % command
        LOG("For %s@%s will run init script asynchronously. Assuming 'at' exists on the target VM" % (username, hostname))

    LOG("For %s@%s EXEC %s" % (username, hostname, command if len(command) <= 80 else command[0:77] + "..."))
    ssh = newSshClient(hostname, username=username, localPrivKey=localPrivKey)

    chan = ssh.get_transport().open_session()
    chan.settimeout(timeout)
    chan.exec_command(command)

    stdin = chan.makefile('wb', -1)
    stdout = chan.makefile('r', -1)
    stderr = chan.makefile_stderr('r', -1)
    exitCode = chan.recv_exit_status()
    stdoutLines = stdout.readlines()
    stderrLines = stderr.readlines()

    stdin.close()
    stdout.close()
    stderr.close()
    ssh.close()

    for line in stdoutLines:
        LOG(">> [%s] STDOUT: %s" % (hostname, line))
    LOG(">> ")
    for line in stderrLines:
        LOG(">> [%s] STDERR: %s" % (hostname, line))

    return exitCode, stdoutLines, stderrLines


def checkSshOnHost(hostname, username="root", localPrivKey=None, timeout=None):
    """
    :type timeout: float
    :rtype : bool
    """
    try:
        LOG("Checking SSH for %s@%s" % (username, hostname))
        ssh = newSshClient(hostname, username=username, localPrivKey=localPrivKey, timeout=timeout)  # 10 sec timeout
    except Exception as e:
        LOG(">> No SSH for %s@%s" % (username, hostname))
        LOGSshException(username, hostname, e)
        return False
    else:
        ssh.close()
        LOG(">> OK SSH for %s@%s" % (username, hostname))
        return True


class OkeanosNativeClient(object):
    def __init__(self, token, authURL='https://accounts.okeanos.grnet.gr/identity/v2.0', typeOfCompute='compute'):
        """
        :type typeOfCompute: str
        :type authURL: str
        :type token: str
        """
        self.authURL = authURL
        self.token = token
        self.typeOfCompute = typeOfCompute
        self.astakosClient = AstakosClient(self.authURL, self.token)
        self.computeEndpoint = self.astakosClient.get_service_endpoints(self.typeOfCompute)
        self.computeURL = self.computeEndpoint[u'publicURL']
        self.cycladesClient = CycladesClient(self.computeURL, self.token)
        flavorsById = {}
        flavorsByName = {}
        for flavor in self.cycladesClient.list_flavors():
            _id = flavor[u'id']
            name = flavor[u'name']
            flavorsById[_id] = name
            flavorsByName[name] = _id
        self.flavorsById = flavorsById
        self.flavorsByName = flavorsByName

    def getFlavorId(self, idOrName):
        """
        :rtype : str
        :type idOrName: str
        """
        if idOrName in self.flavorsById:
            return idOrName
        elif idOrName in self.flavorsByName:
            return self.flavorsByName[idOrName]
        else:
            return idOrName  # caller's responsibility

    def listNodes(self):
        """
        :rtype : list(ListNodeResult)
        """
        instanceInfoList = []
        servers = self.cycladesClient.list_servers()
        for server in servers:
            serverId = str(server[u'id'])  # It is a number in the result
            serverDetails = self.cycladesClient.get_server_details(serverId)
            serverStatusS = serverDetails[u'status']
            serverStatus = NodeStatus(serverStatusS)
            # serverFlavourId = serverDetails[u'flavor'][u'id']
            # serverImageId = serverDetails[u'image'][u'id']
            instanceInfo = ListNodeResult(serverId, serverStatus, serverDetails)
            instanceInfoList.append(instanceInfo)
        return instanceInfoList

    def createNode(self, nodeName, flavorIdOrName, imageId,
                   sshPubKey=None,
                   initScriptPathAndData=None,
                   remoteUsername="root",
                   remoteUsergroup=None,
                   localPubKeyData=None,
                   createAsyncInitScript=True):
        """

        :rtype : NodeDetails
        :type localPubKeyData: str
        :type sshPubKey: str
        :type imageId: str
        :type flavorIdOrName: str
        :type nodeName: str
        """
        LOG("Creating node '%s', %s, %s" % (nodeName, flavorIdOrName, imageId))

        sshPubKey = sshPubKey or None
        if sshPubKey is not None:
            LOG("User SSH public key to be injected in %s: %s" % (nodeName, sshPubKey))
        remoteUsergroup = remoteUsergroup or remoteUsername
        flavorId = self.getFlavorId(flavorIdOrName)

        # We make sure:
        # a) The orchestrator can do password-less SSH on the newly created machine (via ~/.ssh/id_rsa.pub)
        # b) The SlipStream user can do password-less SSH on the newly created machine (via the provided userPubKey)
        # c) The provided init script is injected

        localPubKeyData = localPubKeyData or loadPubRsaKeyData()
        LOG("Local SSH public key to be injected in %s: %s" % (nodeName, localPubKeyData))

        if sshPubKey is None:
            authorized_keys = localPubKeyData
        else:
            if not localPubKeyData.endswith('\n'):
                localPubKeyData += '\n'
            authorized_keys = "%s%s" % (localPubKeyData, sshPubKey)

        # See https://www.synnefo.org/docs/kamaki/latest/developers/showcase.html#inject-ssh-keys
        import base64
        personality = [
            dict(
                contents=base64.b64encode(authorized_keys),
                path="/%s/.ssh/authorized_keys" % remoteUsername,
                owner=remoteUsername,
                group=remoteUsergroup,
                mode=0600
            )
        ]

        if initScriptPathAndData is not None:
            initScriptPath, initScriptData = initScriptPathAndData

            personality.append(
                dict(
                    contents=base64.b64encode(initScriptData),
                    path=initScriptPath,
                    owner=remoteUsername,
                    group=remoteUsergroup,
                    mode=0777
                )
            )

            # In order for the contextualization script to run asynchronously,
            # we create another script that launches the original via nohup
            if createAsyncInitScript:
                asyncInitScriptPath = "%s.async" % initScriptPath
                asyncInitScriptData = "#!/bin/sh -e\nexec nohup %s &\n" % initScriptPath

                personality.append(
                    dict(
                        contents=base64.b64encode(asyncInitScriptData),
                        path=asyncInitScriptPath,
                        owner=remoteUsername,
                        group=remoteUsergroup,
                        mode=0777
                    )
                )
            else:
                asyncInitScriptPath = None
        else:
            initScriptPath = None
            initScriptData = None
            asyncInitScriptPath = None
            asyncInitScriptData = None

        LOG(">> Personalities")
        for _p in personality:
            LOG(">>>> %s" % _p)

        resultDict = self.cycladesClient.create_server(nodeName, flavorId, imageId, personality=personality)
        # No IP is included in this result
        nodeDetails = NodeDetails(resultDict,
                                  sshPubKey=sshPubKey,
                                  initScriptPath=initScriptPath,
                                  initScriptData=initScriptData,
                                  asyncInitScriptPath=asyncInitScriptPath)
        LOG("Created node %s status %s, adminPass = %s, ip4s = %s" % (nodeDetails.id, nodeDetails.status.okeanosStatus, nodeDetails.adminPass, nodeDetails.ipv4s))
        return nodeDetails

    def runCommandOnNode(self, nodeDetails, command,
                         username='root',
                         localPrivKey=None,
                         timeout=None,
                         runSynchronously=True):
        """
        :type timeout: int
        :type localPrivKey: str
        :type nodeDetails: NodeDetails
        :type command: str
        """
        hostname = nodeDetails.ipv4s[0]
        return runCommandOnHost(hostname, command,
                                username=username,
                                localPrivKey=localPrivKey,
                                timeout=timeout,
                                runSynchronously=runSynchronously)

    def checkSshOnNode(self, nodeDetails, username="root", localPrivKey=None, timeout=None):
        hostname = nodeDetails.ipv4s[0]
        return checkSshOnHost(hostname, username=username, localPrivKey=localPrivKey, timeout=timeout)

    def waitSshOnHost(self, hostname, username="root", localPrivKey=None, timeout=None):
        t0 = time.time()
        while True:
            if checkSshOnHost(hostname, username=username, localPrivKey=localPrivKey, timeout=timeout):
                t1 = time.time()
                dtsec = t1 - t0
                LOG("SSH good for %s@%s after %s sec" % (username, hostname, dtsec))
                break

    def waitSshOnNode(self, nodeDetails, username="root", localPrivKey=None, timeout=None):
        hostname = nodeDetails.ipv4s[0]
        self.waitSshOnHost(hostname, username=username, localPrivKey=localPrivKey, timeout=timeout)

    def getNodeDetails(self, nodeId):
        """
        :type nodeId: str
        :rtype : NodeDetails
        """
        resultDict = self.cycladesClient.get_server_details(nodeId)
        nodeDetails = NodeDetails(resultDict)
        return nodeDetails

    def waitNodeStatus(self, nodeId, expectedOkeanosStatus):
        """
        :type expectedOkeanosStatus: str
        :type nodeId: str
        """
        t0 = time.time()
        nodeDetails = self.getNodeDetails(nodeId)
        while nodeDetails.status.okeanosStatus != expectedOkeanosStatus:
            nodeDetails = self.getNodeDetails(nodeId)
        t1 = time.time()
        dtsec = t1 - t0
        LOG("Node %s status %s after %s sec" % (nodeId, expectedOkeanosStatus, dtsec))
        return nodeDetails

    def createNodeAndWait(self, nodeName, flavorIdOrName, imageId, sshPubKey, initScriptPathAndData=None,
                          remoteUsername="root", remoteUsergroup=None, localPubKeyData=None, localPrivKey=None,
                          sshTimeout=None, runInitScriptSynchronously=False):
        """
        :type runInitScriptSynchronously: bool
        :type sshPubKey: str
        :type imageId: str
        :type flavorIdOrName: str
        :type nodeName: str
        :type sshTimeout: float
        :rtype : NodeDetails
        """
        localPrivKey = localPrivKey or loadRsaPrivKey()

        # Note that this returned value (NodeDetails) contains the adminPass
        nodeDetails = self.createNode(nodeName, flavorIdOrName, imageId, sshPubKey,
                                      initScriptPathAndData=initScriptPathAndData,
                                      remoteUsername=remoteUsername,
                                      remoteUsergroup=remoteUsergroup,
                                      localPubKeyData=localPubKeyData)
        nodeId = nodeDetails.id
        nodeDetailsActive = self.waitNodeStatus(nodeId, NodeStatus.ACTIVE)
        nodeDetails.updateIPsAndStatusFrom(nodeDetailsActive)

        # Some times, right after node is reported ACTIVE, network is unreachable or SSH is not immediately ready.
        # We have to cope with that by waiting.
        sshTimeout = sshTimeout or 7.0
        self.waitSshOnNode(nodeDetails, username=remoteUsername, localPrivKey=localPrivKey, timeout=sshTimeout)

        initScriptPath = nodeDetails.initScriptPath

        runResult = self.runCommandOnNode(nodeDetails, initScriptPath,
                                          username=remoteUsername,
                                          localPrivKey=localPrivKey,
                                          runSynchronously=runInitScriptSynchronously)
        return nodeDetails, runResult

    def shutdownNode(self, nodeId):
        """
        :rtype : NodeDetails
        :type nodeId: str
        """
        LOG("Shutting down nodeId %s" % nodeId)
        nodeDetails = self.getNodeDetails(nodeId)
        if not nodeDetails.status.isStopped():
            self.cycladesClient.shutdown_server(nodeId)
            LOG("Shutdown node %s status %s" % (nodeId, nodeDetails.status.okeanosStatus))
        return nodeDetails

    def shutdownNodeAndWait(self, nodeId):
        """
        :rtype : NodeDetails
        :type nodeId: str
        """
        nodeDetails = self.shutdownNode(nodeId)
        if not nodeDetails.status.isStopped():
            nodeDetailsWait = self.waitNodeStatus(nodeId, NodeStatus.STOPPED)
            nodeDetails.updateStatusFrom(nodeDetailsWait)
            LOG("Shutdown node %s status %s" % (nodeId, nodeDetails.status.okeanosStatus))
        return nodeDetails

    def deleteNode(self, nodeId):
        """
        :rtype : NodeDetails
        :type nodeId: str
        """
        LOG("Deleting nodeId %s" % nodeId)
        nodeDetails = self.getNodeDetails(nodeId)
        if not nodeDetails.status.isDeleted():
            self.cycladesClient.delete_server(nodeId)
            LOG("Deleted node %s status %s" % (nodeId, nodeDetails.status.okeanosStatus))
        return nodeDetails

    def deleteNodeAndWait(self, nodeId):
        """
        :rtype : NodeDetails
        :type nodeId: str
        """
        nodeDetails = self.deleteNode(nodeId)
        if not nodeDetails.status.isDeleted():
            nodeDetailsWait = self.waitNodeStatus(nodeId, NodeStatus.DELETED)
            nodeDetails.updateStatusFrom(nodeDetailsWait)
            LOG("Deleted node %s status %s" % (nodeId, nodeDetails.status.okeanosStatus))
        return nodeDetails
