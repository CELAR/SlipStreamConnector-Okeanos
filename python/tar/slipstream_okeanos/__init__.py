"""
 Copyright (c) 2014 GRNET SA (grnet.gr)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import tempfile
from kamaki.clients.astakos import AstakosClient
from kamaki.clients.cyclades import CycladesClient, CycladesBlockStorageClient
import time
import socket
import inspect


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
    :rtype : paramiko.rsakey.RSAKey
    :type name: str
    """
    import os.path as ospath
    from paramiko.rsakey import RSAKey
    filename = ospath.expanduser("~/.ssh/%s" % name)
    LOG("Loading SSH private key from %s" % filename)
    rsaKey = RSAKey(filename=filename)
    return rsaKey


def loadRsaPrivKeyData(name="id_rsa"):
    """
    :rtype : str
    :type name: str
    """
    import os.path as ospath
    filename = ospath.expanduser("~/.ssh/%s" % name)
    LOG("Loading SSH private key data from %s" % filename)
    with open(filename, 'r') as f:
        return f.read()


def loadPubRsaKeyData(name="id_rsa.pub"):
    """
    :type name: str
    """
    import os.path as ospath
    filename = ospath.expanduser("~/.ssh/%s" % name)
    LOG("Loading SSH public key data from %s" % filename)
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


def newSftpClient(hostname, username="root", localPrivKey=None, timeout=None, ssh=None):
    """
    :rtype : paramiko.sftp_client.SFTPClient
    """
    if ssh is None:
        ssh = newSshClient(hostname, username=username, localPrivKey=localPrivKey, timeout=timeout)
    return ssh.open_sftp()


def newTmpFileWithScriptData(scriptData):
    fd, scriptFile = tempfile.mkstemp()
    os.write(fd, scriptData)
    os.close(fd)
    os.chmod(scriptFile, 0755)
    return scriptFile


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


def getHostPartitions(hostname,
                      username='root',
                      localPrivKey=None,
                      timeout=None,
                      ssh=None):
    """
    Retrieve the partitions according to /proc/partitions.
    See http://www.tldp.org/HOWTO/Partition-Mass-Storage-Definitions-Naming-HOWTO/x160.html
    """
    command = "/bin/bash -c 'cat /proc/partitions | sed 1d | sed /^\\$/d | awk \\'{print $4}\\''"
    LOG("> host = %s, running %s" % (hostname, command))
    exitCode, stdoutLines, stderrLines = runCommandOnHost(hostname, command,
                                                          username=username,
                                                          localPrivKey=localPrivKey,
                                                          timeout=timeout,
                                                          ssh=ssh)
    status = exitCode
    device_list = [line.rstrip() for line in stdoutLines]   # remove trailing '\n'
    devices = set(device_list)
    LOG("< status = %s, devices = %s" % (status, devices))
    return status, devices


def runCommandOnHost(hostname, command,
                     username='root',
                     localPrivKey=None,
                     timeout=None,
                     runSynchronously=True,
                     ssh=None):
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

    if ssh is None:
        ssh = newSshClient(hostname, username=username, localPrivKey=localPrivKey)
    else:
        LOG("Reusing ssh client")

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


def runScriptDataOnHost(hostname, scriptData, remoteScriptFile,
                        username='root',
                        localPrivKey=None,
                        timeout=None,
                        runSynchronously=True,
                        ssh=None):
    """
    :type remoteScriptFile: str
    :type timeout: int
    :type localPrivKey: str
    :type hostname: strs
    :type command: str
    """
    localScriptFile = newTmpFileWithScriptData(scriptData)
    sftp = newSftpClient(hostname, username=username, ssh=ssh)
    LOG("Copying %s to %s@%s:%s" % (localScriptFile, username, hostname, remoteScriptFile))
    result = sftp.put(localScriptFile, remoteScriptFile)
    LOG("result = %s" % result)
    sftp.close()
    os.unlink(localScriptFile)

    if remoteScriptFile.startswith("/"):
        remoteCommand = remoteScriptFile
    else:
        remoteCommand = "~/%s" % remoteScriptFile

    return runCommandOnHost(hostname, remoteCommand,
                            username=username,
                            localPrivKey=localPrivKey,
                            timeout=timeout,
                            ssh=ssh,
                            runSynchronously=runSynchronously)


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
    def __init__(self, token, authURL='https://accounts.okeanos.grnet.gr/identity/v2.0'):
        """
        :type authURL: str
        :type token: str
        """
        from kamaki.clients.utils import https
        https.patch_ignore_ssl()

        self.authURL = authURL
        self.token = token
        self.cycladesServiceType = CycladesClient.service_type
        self.blockStorageServiceType = CycladesBlockStorageClient.service_type
        self.astakosClient = AstakosClient(self.authURL, self.token)
        endpointF = self.astakosClient.get_service_endpoints
        self.cycladesEndpoint = endpointF(self.cycladesServiceType)[u'publicURL']
        self.cycladesClient = CycladesClient(self.cycladesEndpoint, self.token)
        self.blockStorageEndpoint = endpointF(self.blockStorageServiceType)[u'publicURL']
        self.blockStorageClient = CycladesBlockStorageClient(self.blockStorageEndpoint, token)

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

    def createVolume(self, serverId, sizeGB, projectId):
        """
        :param serverId: str
        :param sizeGB: Union[str, int]
        :param projectId: str
        :rtype str
        """
        self.log("> serverId=%s, sizeGB=%s, projectId=%s" % (serverId, sizeGB, projectId))

        response = self.blockStorageClient.create_volume(sizeGB,
                                                         serverId,
                                                         '%s-vol-%s' % (serverId, sizeGB),
                                                         project=projectId)
        # response is something like this
        # {
        #     u'display_name': u'foo',
        #     u'id': u'46974',
        #     u'links': [
        #         {
        #             u'href': u'https://cyclades.okeanos.grnet.gr/volume/v2.0/volumes/46974',
        #             u'rel': u'self'
        #         }, {
        #             u'href': u'https://cyclades.okeanos.grnet.gr/volume/v2.0/volumes/46974',
        #             u'rel': u'bookmark'
        #         }
        #     ]
        # }

        self.log("< %s" % response)

        return response

    def attachVolume(self, serverId, sizeGB, projectId):
        """Create and attach an extra volume to the VM, returning the volume name, the volume id and the device name"""
        self.log("> serverId = %s, sizeGB = %s, projectId = %s" % (serverId, sizeGB, projectId))

        _, partitions0 = self.getNodePartitions(serverId)
        result = self.createVolume(serverId, sizeGB, projectId)

        # NOTE we use default stuff fro SSH here!
        new_partition = self.waitForExtraNodePartition(serverId, partitions0)
        # TODO Check if None

        volumeName = result['display_name']
        volumeId = result['id']
        deviceName = "/dev/%s" % new_partition

        result = (volumeName, volumeId, deviceName)
        self.log("< volumeName = %s, volumeId = %s, deviceName = %s" % result)
        return result

    def deleteVolume(self, volumeId):
        """
        Deletes the volume identified by the given `volumeId`.
        :param volumeId: str
        :return:
        """
        response = self.blockStorageClient.delete_volume(volumeId)
        return response

    def createNode(self, nodeName, flavorIdOrName, imageId,
                   sshPubKey=None,
                   initScriptPathAndData=None,
                   remoteUsername="root",
                   remoteUsergroup=None,
                   localPubKeyData=None,
                   createAsyncInitScript=True,
                   projectId=None):
        """

        :rtype : NodeDetails
        :type localPubKeyData: str
        :type sshPubKey: str
        :type imageId: str
        :type flavorIdOrName: str
        :type nodeName: str
        """
        self.log("Creating node '%s', %s, %s" % (nodeName, flavorIdOrName, imageId))

        sshPubKey = sshPubKey or None
        if sshPubKey is not None:
            self.log("User SSH public key to be injected in %s: %s" % (nodeName, sshPubKey))
        remoteUsergroup = remoteUsergroup or remoteUsername
        flavorId = self.getFlavorId(flavorIdOrName)

        # We make sure:
        # a) The orchestrator can do password-less SSH on the newly created machine (via ~/.ssh/id_rsa.pub)
        # b) The SlipStream user can do password-less SSH on the newly created machine (via the provided userPubKey)
        # c) The provided init script is injected

        localPubKeyData = localPubKeyData or loadPubRsaKeyData()
        self.log("Local SSH public key to be injected in %s: %s" % (nodeName, localPubKeyData))

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

        self.log(">> Personalities")
        for _p in personality:
            self.log(">>>> %s" % _p)

        resultDict = self.cycladesClient.create_server(nodeName,
                                                       flavorId,
                                                       imageId,
                                                       personality=personality,
                                                       project_id=projectId)
        # No IP is included in this result
        nodeDetails = NodeDetails(resultDict,
                                  sshPubKey=sshPubKey,
                                  initScriptPath=initScriptPath,
                                  initScriptData=initScriptData,
                                  asyncInitScriptPath=asyncInitScriptPath)
        self.log("Created node %s status %s, adminPass = %s, ip4s = %s" % (nodeDetails.id, nodeDetails.status.okeanosStatus, nodeDetails.adminPass, nodeDetails.ipv4s))
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
                self.log("SSH good for %s@%s after %s sec" % (username, hostname, dtsec))
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
        self.log("Node %s status %s after %s sec" % (nodeId, expectedOkeanosStatus, dtsec))
        return nodeDetails

    def createNodeAndWait(self, nodeName, flavorIdOrName, imageId, sshPubKey, initScriptPathAndData=None,
                          remoteUsername="root", remoteUsergroup=None, localPubKeyData=None, localPrivKey=None,
                          sshTimeout=None, runInitScriptSynchronously=False,
                          extraVolatileDiskGB=0, projectId=None):
        """

        :type extraVolatileDiskGB: int
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
                                      localPubKeyData=localPubKeyData,
                                      projectId=projectId)
        nodeId = nodeDetails.id
        nodeDetailsActive = self.waitNodeStatus(nodeId, NodeStatus.ACTIVE)
        nodeDetails.updateIPsAndStatusFrom(nodeDetailsActive)

        # attach any additional disk
        hostIP = nodeDetails.ipv4s[0]
        if extraVolatileDiskGB:
            self.log("Creating volatile disk of size %s GB for machine IP=%s, id=%s" % (extraVolatileDiskGB, hostIP, nodeId))
            volumeId = self.createVolume(nodeId, extraVolatileDiskGB)
            self.log("Created volumeId=%s of size %s GB for machine IP=%s, id=%s" % (volumeId, extraVolatileDiskGB, hostIP, nodeId))
            # We do nothing more with the volumeId.
            # When the VM is destroyed by the IaaS, the extra disk is automatically destroyed as well.
        else:
            self.log("No need for extra volatile disk for machine IP=%s, id=%s" % (hostIP, nodeId))

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
        self.log("Shutting down nodeId %s" % nodeId)
        nodeDetails = self.getNodeDetails(nodeId)
        if not nodeDetails.status.isStopped():
            self.cycladesClient.shutdown_server(nodeId)
            self.log("Shutdown node %s status %s" % (nodeId, nodeDetails.status.okeanosStatus))
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
            self.log("Shutdown node %s status %s" % (nodeId, nodeDetails.status.okeanosStatus))
        return nodeDetails

    def deleteNode(self, nodeId):
        """
        :rtype : NodeDetails
        :type nodeId: str
        """
        self.log("Deleting nodeId %s" % nodeId)
        nodeDetails = self.getNodeDetails(nodeId)
        if not nodeDetails.status.isDeleted():
            self.cycladesClient.delete_server(nodeId)
            self.log("Deleted node %s status %s" % (nodeId, nodeDetails.status.okeanosStatus))
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
            self.log("Deleted node %s status %s" % (nodeId, nodeDetails.status.okeanosStatus))
        return nodeDetails

    def log(self, msg=''):
        who = '%s::%s' % (self.__class__.__name__, inspect.stack()[1][3])
        LOG('%s# %s' % (who, msg))

    def getNodeIPv4(self, nodeId):
        nodeDetails = self.getNodeDetails(nodeId)
        ipv4 = nodeDetails.ipv4s[0]
        LOG("< for nodeId = %s, IPv4 = %s" % (nodeId, ipv4))
        return ipv4

    def getNodePartitions(self, nodeId,
                          username='root',
                          localPrivKey=None,
                          timeout=None,
                          ssh=None):
        ipv4 = self.getNodeIPv4(nodeId)
        status, partitions = getHostPartitions(ipv4,
                                               username=username,
                                               localPrivKey=localPrivKey,
                                               timeout=timeout,
                                               ssh=ssh)
        return status, partitions

    def waitForExtraNodePartition(self, serverId, partitions,
                                  username='root',
                                  localPrivKey=None,
                                  timeout=None,
                                  ssh=None):
        """
        Given the set of pre-existing partitions, we wait until a new one appears and then we return it.
        :param serverId: str
        :param partitions: set[str]
        :return: the extra partition. prepend '/dev/' to get the device name
        """
        def getem():
            return self.getNodePartitions(serverId,
                                          username=username,
                                          localPrivKey=localPrivKey,
                                          timeout=timeout,
                                          ssh=ssh)

        self.log("Waiting, current partitions: %s" % partitions)
        status1, partitions1 = getem()
        if status1 != 0:
            return None

        while partitions == partitions1:
            self.log("Looping, new partitions: %s" % partitions1)
            status1, partitions1 = getem()
            if status1 != 0:
                return None

        # We assume one more is added ...
        newPartition = partitions1.difference(partitions)
        self.log("< For serverId = %s, new partition = %s" % (serverId, newPartition))
        return newPartition
