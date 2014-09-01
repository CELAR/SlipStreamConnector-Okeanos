"""
 SlipStream Client
 =====
 Copyright (C) 2013 SixSq Sarl (sixsq.com)
 =====
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

# pylint: disable=C0111


from slipstream.cloudconnectors.BaseCloudConnector import BaseCloudConnector
from slipstream.NodeDecorator import KEY_RUN_CATEGORY
from sliplstream_okeanos import LOG, OkeanosNativeClient, loadPubRsaKeyData, NodeStatus
import slipstream.exceptions.Exceptions as Exceptions


def getConnector(configHolder):
    return getConnectorClass()(configHolder)


def getConnectorClass():
    return OkeanosClientCloud


class OkeanosClientCloud(BaseCloudConnector):
    cloudName = 'okeanos'

    def __init__(self, configHolder):
        LOG("OkeanosClientCloud::__init__# configHolder = %s" % configHolder.config)
        self.run_category = getattr(configHolder, KEY_RUN_CATEGORY, None)
        LOG("OkeanosClientCloud::__init__# self.run_category = %s" % self.run_category)

        super(OkeanosClientCloud, self).__init__(configHolder)
        LOG("OkeanosClientCloud::__init__# self.cloud = %s" % self.cloud)

        self.setCapabilities(contextualization=True, orchestrator_can_kill_itself_or_its_vapp=True)

        self.okeanosAuthURL = None
        self.okeanosUUID = None
        self.okeanosToken = None
        self.okeanosClient = None


    def makeCloudKey(self, key):
        """
        :rtype : str
        :type key: str
        """
        prefix = self.cloud + "."
        if key.startswith(prefix):
            return key
        else:
            return prefix + key


    def initialization(self, userInfo):
        # userInfo =
        # {
        #   'okeanos.endpoint': 'https://accounts.okeanos.grnet.gr/identity/v2.0',
        #   'okeanos.username': '==UUID==',
        #   'okeanos.password': '==TOKEN=='
        #   'okeanos.service.type': 'compute',
        #   'okeanos.service.name': 'cyclades_compute',
        #   'okeanos.orchestrator.instance.type': 'C2R2048D10ext_vlmc',
        #   'okeanos.orchestrator.imageid': '6b1c431a-d18c-4609-b4d9-3f29acce2c1f',
        #   'okeanos.service.region': 'default',
        #   'User.email': 'super',
        #   'User.lastName': 'Administrator',
        #   'User.firstName': 'SixSq',
        #   'General.ssh.public.key': 'ssh-rsa USER-PROVIDED PUBLIC SSH KEY\n',
        #   'General.On Error Run Forever': 'false',
        #   'General.Timeout': '30',
        #   'General.On Success Run Forever': 'true',
        #   'General.orchestrator.publicsshkey': 'ssh-rsa root@snf-XYZ PUBLIC SSH KEY (Orchestrator)\n',
        #   'General.default.cloud.service': 'okeanos',
        #   'General.Verbosity Level': '3',
        # }


        LOG("OkeanosClientCloud::initialization# user_info = %s" % userInfo)
        self.okeanosAuthURL = userInfo[self.makeCloudKey('endpoint')]
        self.okeanosUUID = userInfo[self.makeCloudKey('username')]
        self.okeanosToken = userInfo[self.makeCloudKey('password')]
        self.okeanosClient = OkeanosNativeClient(self.okeanosToken, self.okeanosAuthURL)

        LOG("OkeanosClientCloud::initialization# self.okeanosAuthURL = %s" % self.okeanosAuthURL)
        LOG("OkeanosClientCloud::initialization# self.okeanosUUID = %s" % self.okeanosUUID)
        LOG("OkeanosClientCloud::initialization# self.okeanosToken = %s" % self.okeanosToken)


    def finalization(self, user_info):
        LOG("OkeanosClientCloud::finalization# NOOP")
        pass

    def _buildImage(self, userInfo, imageInfo):
        msg = "Build image not supported for %s" % self.cloud
        LOG("OkeanosClientCloud::_buildImage# Will raise '%s'" % msg)
        raise Exception(msg)

    def _startImage(self, userInfo, imageInfo, nodeName, initScriptData=None):
        # imageInfo =
        # {
        #   'attributes': {
        #       'category': 'Image',
        #       'resourceUri': 'module/P5/I5/14',
        #       'name': 'P5/I5',
        #       'parentUri': 'module/P5',
        #       'deleted': 'false',
        #       'lastModified': '2014-05-30 16:03:15.741 EEST',
        #       'creation': '2014-05-30 16:03:15.717 EEST',
        #       'isLatestVersion': 'true',
        #       'imageId': '6b1c431a-d18c-4609-b4d9-3f29acce2c1f',
        #       'platform': 'ubuntu',
        #       'version': '14',
        #       'loginUser': '',
        #       'isBase': 'true',
        #       'shortName': 'I5'
        #   },
        #   'extra_disks': {},
        #   'targets': {},
        #   'cloud_parameters': {
        #       'openstack': {
        #           'openstack.security.groups': 'default',
        #           'openstack.instance.type': None
        #       },
        #       'Cloud': {
        #           'network': 'Public'
        #       },
        #       'okeanos': {
        #           'okeanos.security.groups': 'default',
        #           'okeanos.instance.type': 'C2R2048D10ext_vlmc'
        #       }
        #   }
        # }
        """
        :param userInfo:
        :param imageInfo:
        :param nodeName:
        :param initScriptData: The initialization script
        :return: :raise Exception:
        """
        LOG("OkeanosClientCloud::_startImage#")
        LOG("OkeanosClientCloud::_startImage# userInfo = %s" % userInfo)
        LOG("OkeanosClientCloud::_startImage# imageInfo = %s" % imageInfo)
        LOG("OkeanosClientCloud::_startImage# nodeName = %s" % nodeName)
        LOG("OkeanosClientCloud::_startImage# initScriptData = %s" % initScriptData)

        imageId = self.getImageId(imageInfo)
        flavorIdOrName = self._getInstanceType(imageInfo)  # imageInfo['cloud_parameters'][self.cloud][self.cloudKey('instance.type')]
        sshPubKey = userInfo.get('General.ssh.public.key')
        initScriptPath = "/root/okeanosNodeInitScript"
        if initScriptData is None:
            initScriptPathAndData = None
        else:
            initScriptPathAndData = (initScriptPath, initScriptData)

        remoteUsername = "root"  # TODO make it configurable
        localPubKeyData = loadPubRsaKeyData()
        runInitScriptSynchronously = False  # TODO make it configurable

        if flavorIdOrName is None:
            raise Exceptions.ParameterNotFoundException("Couldn't find the specified flavor: %s" % flavorIdOrName)
        if imageId is None:
            raise Exceptions.ParameterNotFoundException("Couldn't find the specified image: %s" % imageId)

        # We need to run the initScript manually, since ~Okeanos does not support it.
        # Let's wait until we have SSH and then run the script.
        nodeDetails, scriptResults = self.okeanosClient.createNodeAndWait(nodeName, flavorIdOrName, imageId,
                                                                          sshPubKey,
                                                                          initScriptPathAndData=initScriptPathAndData,
                                                                          remoteUsername=remoteUsername,
                                                                          localPubKeyData=localPubKeyData,
                                                                          runInitScriptSynchronously=runInitScriptSynchronously)
        scriptExitCode, scriptStdoutLines, scriptStderrLines = scriptResults
        hostname = nodeDetails.ipv4s[0]
        for line in scriptStdoutLines:
            LOG("[%s] #STDOUT# %s" % (hostname, line))
        for line in scriptStderrLines:
            LOG("[%s] #STDERR# %s" % (hostname, line))

        vm = dict(
            networkType='Public',  # self.getCloudParameters(image_info)['network']
            instance=nodeDetails,
            ip='',
            id=nodeDetails.id
        )

        return vm

    def _getCloudSpecificData(self, nodeInfo, nodeNumber, nodeName):
        # nodeInfo =
        # {
        #   'multiplicity': 1,
        #   'image': {
        #       'attributes': {
        #           'category': 'Image',
        #           'resourceUri': 'module/P5/I5/14',
        #           'name': 'P5/I5',
        #           'parentUri': 'module/P5',
        #           'deleted': 'false',
        #           'lastModified': '2014-05-30 16:03:15.741 EEST',
        #           'creation': '2014-05-30 16:03:15.717 EEST',
        #           'isLatestVersion': 'true',
        #           'imageId': '6b1c431a-d18c-4609-b4d9-3f29acce2c1f',
        #           'platform': 'ubuntu',
        #           'version': '14',
        #           'loginUser': '',
        #           'isBase': 'true',
        #           'shortName': 'I5'
        #       },
        #       'extra_disks': {},
        #       'targets': {},
        #       'cloud_parameters': {
        #           'openstack': {
        #               'openstack.security.groups': 'default',
        #               'openstack.instance.type': None
        #           },
        #           'Cloud': {
        #               'network': 'Public'
        #           },
        #           'okeanos': {
        #               'okeanos.security.groups': 'default',
        #               'okeanos.instance.type': 'C2R2048D10ext_vlmc'
        #           }
        #       }
        #   },
        #   'cloudService': 'okeanos',
        #   'nodename': 'Server'
        # }
        LOG("OkeanosClientCloud::_getCloudSpecificData# ")
        LOG("OkeanosClientCloud::_getCloudSpecificData# nodeInfo = %s" % nodeInfo)
        LOG("OkeanosClientCloud::_getCloudSpecificData# nodeNumber = %s" % nodeNumber)
        LOG("OkeanosClientCloud::_getCloudSpecificData# nodeName = %s" % nodeName)
        script = self._getBootstrapScript(nodeName)
        LOG("OkeanosClientCloud::_getCloudSpecificData# script =\n%s" % script)
        return script

    def stopDeployment(self):
        LOG("OkeanosClientCloud::stopDeployment#")
        for _, vm in self.getVms().items():
            nodeDetails = vm['instance']
            nodeId = nodeDetails.id
            nodeName = nodeDetails.name
            LOG("OkeanosClientCloud::stopDeployment# Stopping %s (%s)" % (nodeId, nodeName))
            self.okeanosClient.deleteNodeAndWait(nodeId)

    def stopVmsByIds(self, ids):
        LOG("OkeanosClientCloud::stopVmsByIds#")
        LOG("OkeanosClientCloud::stopVmsByIds# ids = %s" % ids)
        for nodeId in ids:
            LOG("OkeanosClientCloud::stopVmsByIds# Delete VM %s" % nodeId)
            self.okeanosClient.deleteNode(nodeId)

    def vmGetIp(self, vm):
        return vm['ip']

    def vmGetId(self, vm):
        return vm['id']

    def _waitAndGetInstanceIpAddress(self, vm):
        # vm =
        # {
        #   'ip': '',
        #   'instance': <slipstream.cloudconnectors.okeanos.NodeDetails object at 0x0000000>,
        #   'id': '549929',
        #   'networkType': 'Public'
        # }
        LOG("OkeanosClientCloud::_waitAndGetInstanceIpAddress# vm = %s" % vm)
        nodeDetails = vm['instance']
        nodeId = nodeDetails.id
        nodeDetailsActive = self.okeanosClient.waitNodeStatus(nodeId, NodeStatus.ACTIVE)
        nodeDetails.updateIPsAndStatusFrom(nodeDetailsActive)
        ip = nodeDetails.ipv4s[0]

        # Wait for SSH connectivity
        remoteUsername = "root"
        sshTimeout = 7.0
        self.okeanosClient.waitSshOnNode(nodeDetails, username=remoteUsername, timeout=sshTimeout)

        LOG("OkeanosClientCloud::_waitAndGetInstanceIpAddress# id = %s, ip = %s, adminPass = %s" % (nodeId, ip, nodeDetails.adminPass))

        if ip:
            vm['ip'] = ip
            LOG("OkeanosClientCloud::_waitAndGetInstanceIpAddress# vm = %s" % vm)
            return vm

        raise Exceptions.ExecutionException('Timed out while waiting for IPs to be assigned to instances: %s' % nodeId)
