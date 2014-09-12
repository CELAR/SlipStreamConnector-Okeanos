"""
 SlipStream Client
 =====
 Copyright (C) 2014 SixSq Sarl (sixsq.com)
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

import inspect

from slipstream.cloudconnectors.BaseCloudConnector import BaseCloudConnector
from slipstream.NodeDecorator import KEY_RUN_CATEGORY
from . import LOG, OkeanosNativeClient, loadPubRsaKeyData, NodeStatus
import slipstream.exceptions.Exceptions as Exceptions


def getConnector(configHolder):
    return getConnectorClass()(configHolder)


def getConnectorClass():
    return OkeanosClientCloud


class OkeanosClientCloud(BaseCloudConnector):
    cloudName = 'okeanos'

    def __init__(self, configHolder):
        self.log(configHolder.config)
        self.run_category = getattr(configHolder, KEY_RUN_CATEGORY, None)
        self.log("self.run_category = %s" % self.run_category)

        super(OkeanosClientCloud, self).__init__(configHolder)
        self.log("self.cloud = %s" % self.get_cloud_service_name())

        self._set_capabilities(contextualization=True, orchestrator_can_kill_itself_or_its_vapp=True)

        self.okeanosAuthURL = None
        self.okeanosUUID = None
        self.okeanosToken = None
        self.okeanosClient = None

    def _initialization(self, user_info):
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

        self.log("user_info = %s" % user_info)
        self.okeanosAuthURL = user_info.get_cloud_endpoint()
        self.okeanosUUID = user_info.get_cloud_username()
        self.okeanosToken = user_info.get_cloud_password()
        self.okeanosClient = OkeanosNativeClient(self.okeanosToken, self.okeanosAuthURL)

        self.log("self.okeanosAuthURL = %s" % self.okeanosAuthURL)
        self.log("self.okeanosUUID = %s" % self.okeanosUUID)
        self.log("self.okeanosToken = %s" % self.okeanosToken)

    def _finalization(self, user_info):
        self.log("NOOP")

    def _build_image(self, user_info, node_instance):
        msg = "Build image not supported for %s" % self.get_cloud_service_name()
        self.log("Will raise '%s'" % msg)
        raise NotImplementedError(msg)

    def _start_image(self, user_info, node_instance, vm_name):
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
        :param user_info:  UserInfo object
        :param node_instance:  NodeInstance object
        :param vm_name: string
        :return: :raise Exception:
        """
        self.log()
        self.log("user_info = %s" % user_info)
        self.log("node_instance = %s" % node_instance)
        self.log("vm_name = %s" % vm_name)
        initScriptData = self._get_init_script(node_instance)
        self.log("initScriptData = %s" % initScriptData)

        imageId = node_instance.get_image_id()
        flavorIdOrName = node_instance.get_instance_type()
        sshPubKey = user_info.get_public_keys()
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
        # TODO: Provide network type.
        nodeDetails, scriptResults = self.okeanosClient.createNodeAndWait(
            vm_name, flavorIdOrName, imageId,
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

    def _get_init_script(self, node_instance):
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
        self.log()
        self.log("nodeInfo = %s" % node_instance)
        script = self._get_bootstrap_script(node_instance)
        self.log("script =\n%s" % script)
        return script

    def _stop_deployment(self):
        self.log()
        for _, vm in self.get_vms().items():
            nodeDetails = vm['instance']
            nodeId = nodeDetails.id
            nodeName = nodeDetails.name
            self.log("Stopping %s (%s)" % (nodeId, nodeName))
            self.okeanosClient.deleteNodeAndWait(nodeId)

    def _stop_vms_by_ids(self, ids):
        self.log()
        self.log("ids = %s" % ids)
        for nodeId in ids:
            self.log("Delete VM %s" % nodeId)
            self.okeanosClient.deleteNode(nodeId)

    def _vm_get_ip(self, vm):
        return vm['ip']

    def _vm_get_id(self, vm):
        return vm['id']

    def _wait_and_get_instance_ip_address(self, vm):
        # vm =
        # {
        #   'ip': '',
        #   'instance': <slipstream.cloudconnectors.okeanos.NodeDetails object at 0x0000000>,
        #   'id': '549929',
        #   'networkType': 'Public'
        # }
        self.log("vm = %s" % vm)
        nodeDetails = vm['instance']
        nodeId = nodeDetails.id
        nodeDetailsActive = self.okeanosClient.waitNodeStatus(nodeId, NodeStatus.ACTIVE)
        nodeDetails.updateIPsAndStatusFrom(nodeDetailsActive)
        ip = nodeDetails.ipv4s[0]

        # Wait for SSH connectivity
        remoteUsername = "root"
        sshTimeout = 7.0
        self.okeanosClient.waitSshOnNode(nodeDetails, username=remoteUsername, timeout=sshTimeout)

        self.log("id = %s, ip = %s, adminPass = %s" % (nodeId, ip, nodeDetails.adminPass))

        if ip:
            vm['ip'] = ip
            self.log("vm = %s" % vm)
            return vm

        raise Exceptions.ExecutionException('Timed out while waiting for IPs to be assigned to instances: %s' % nodeId)

    def log(self, msg=''):
        who = '%s::%s' % (self.__class__.__name__, inspect.stack()[1][3])
        LOG('%s# %s' % (who, msg))
