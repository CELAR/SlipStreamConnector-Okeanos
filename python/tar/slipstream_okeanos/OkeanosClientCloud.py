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

# pylint: disable=C0111

import inspect

from slipstream.cloudconnectors.BaseCloudConnector import BaseCloudConnector
from slipstream.NodeDecorator import KEY_RUN_CATEGORY
from . import LOG, OkeanosNativeClient, loadPubRsaKeyData, NodeStatus, runScriptDataOnHost
from slipstream.exceptions import Exceptions
from slipstream_okeanos import ListNodeResult


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
        # 'okeanos.endpoint': 'https://accounts.okeanos.grnet.gr/identity/v2.0',
        # 'okeanos.username': '==UUID==',
        #   'okeanos.password': '==TOKEN=='
        #   'okeanos.project.id': '==PROJECT ID=='
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

        from kamaki.clients.utils import https
        https.patch_ignore_ssl()

        self.log("user_info = %s" % user_info)
        self.okeanosAuthURL = user_info.get_cloud_endpoint()
        self.okeanosUUID = user_info.get_cloud_username()
        self.okeanosToken = user_info.get_cloud_password()
        self.okeanosProjectId = user_info.get_cloud('project.id')
        self.okeanosClient = OkeanosNativeClient(self.okeanosToken, self.okeanosAuthURL)

        self.log("self.okeanosAuthURL = %s" % self.okeanosAuthURL)
        self.log("self.okeanosUUID = %s" % self.okeanosUUID)
        self.log("self.okeanosToken = %s" % self.okeanosToken)

    def _finalization(self, user_info):
        self.log("NOOP")

    def __get_ssh_private_key_file(self, user_info):
        import os.path as ospath

        return ospath.expanduser("~/.ssh/id_rsa")

    def __get_vm_username_password(self, node_instance, default_user='root'):
        username = node_instance.get_username(default_user)
        password = None
        self.log("username = %s, password = %s" % (username, password))
        return username, password

    def _get_ssh_credentials(self, node_instance, user_info):
        username, password = self.__get_vm_username_password(node_instance)
        if password:
            ssh_private_key_file = None
        else:
            ssh_private_key_file = self.__get_ssh_private_key_file(user_info)
        self.log("username = %s, password = %s, ssh_private_key_file = %s" % (username, password, ssh_private_key_file))
        return username, password, ssh_private_key_file

    def _build_image(self, userInfo, nodeInstance):
        """
        :rtype : str
        :type userInfo: slipstream.UserInfo.UserInfo
        :type nodeInstance: slipstream.NodeInstance.NodeInstance
        """

        # userInfo = {
        # "okeanos.username": "UUID",
        #  "okeanos.max.iaas.workers": "20",
        #  "okeanos.quota.vm": "",
        #  "okeanos.service.name": "cyclades_compute",
        #  "General.On Error Run Forever": "true",
        #  "General.Timeout": "30",
        #  "General.On Success Run Forever": "true",
        #  "General.orchestrator.publicsshkey": "ssh-rsa LOCALKEY root@snf-000000\n",
        #  "okeanos.orchestrator.instance.type": "C2R2048D10ext_vlmc",
        #  "okeanos.orchestrator.imageid": "fe31fced-a3cf-49c6-b43b-f58f5235ba45",
        #  "User.email": "super@sixsq.com",
        #  "General.default.cloud.service": "okeanos",
        #  "okeanos.endpoint": "https://accounts.okeanos.grnet.gr/identity/v2.0",
        #  "User.lastName": "User",
        #  "okeanos.update.clienturl": "https://IP/downloads/okeanoslibs.tar.gz",
        #  "User.firstName": "Super",
        #  "okeanos.service.region": "default",
        #  "General.ssh.public.key": "ssh-rsa  TESTSSHKEY\n",
        #  "okeanos.service.type": "compute",
        #  "General.Verbosity Level": "3",
        #  "okeanos.password": "TOKEN",
        #  "okeanos.private.key": None
        #}

        # nodeInstance = NodeInstance({
        #  "image.parentUri": "module/P5",
        #  "image.shortName": "B2",
        #  "image.logoLink": "",
        #  "abort": null,
        #  "image.deleted": "false",
        #  "image.category": "Image",
        #  "image.class": "com.sixsq.slipstream.persistence.ImageModule",
        #  "image.version": "7",
        #  "okeanos.security.groups": "default",
        #  "okeanos.instance.type": "C2R2048D10ext_vlmc",
        #  "extra.disk.volatile": None,
        #  "image.platform": "ubuntu",
        #  "network": "Public",
        #  "image.moduleReferenceUri": "module/P5/B1",
        #  "hostname": None,
        #  "image.lastModified": "2014-09-18 17:06:18.915 EEST",
        #  "is.orchestrator": "false",
        #  "url.service": None,
        #  "statecustom": None,
        #  "image.isBase": "false",
        #  "complete": "false",
        #  "image.resourceUri": "module/P5/B2/7",
        #  "image.id": "fe31fced-a3cf-49c6-b43b-f58f5235ba45",
        #  "image.loginUser": "root",
        #  "image.isLatestVersion": "true",
        #  "scale.state": "creating",
        #  "image.packages": [],
        #  "image.name": "P5/B2",
        #  "name": "machine",
        #  "instanceid": None,
        #  "cloudservice": "okeanos",
        #  "image.recipe": "#!/bin/sh\n\necho BuildImage > /root/BuildImage.txt\n",
        #  "url.ssh": None,
        #  "image.creation": "2014-09-18 17:05:27.995 EEST",
        #  "image.prerecipe": "",
        #  "vmstate": "Unknown",
        #  "image.description": ""
        #})

        self.log()
        self.log("userInfo = %s" % userInfo)
        self.log("nodeInstance = %s" % nodeInstance)

        machine_name = nodeInstance.get_name()
        vm = self._get_vm(machine_name)
        ip = self._vm_get_ip(vm)
        # nodeDetails = vm['instance']

        remoteUsername = nodeInstance.get_image_attribute("loginUser", default_value="root")
        self.log("ip = %s, remoteUsername = %s" % (ip, remoteUsername))
        self.okeanosClient.waitSshOnHost(ip, username=remoteUsername)

        self.log("Running _build_image_increment(), that is: prerecipe, packages, recipe")
        prerecipe = nodeInstance.get_prerecipe()
        runScriptDataOnHost(ip, prerecipe, "prerecipe", username=remoteUsername)
        recipe = nodeInstance.get_recipe()
        runScriptDataOnHost(ip, recipe, "recipe", username=remoteUsername)

        self._build_image_increment(userInfo, nodeInstance, ip)

        self.log("FINALLY creating the new image")

        imageCategory = nodeInstance.get_image_attribute("category")  # Image
        imageResourceUri = nodeInstance.get_image_attribute("resourceUri")  # P5/B2/7
        newImageName = "%s.%s" % (imageCategory, imageResourceUri.replace("/", "."))  # Image.P5.B2.7

        snfMkImageScriptData = "#!/bin/sh"
        snfMkImageScriptData += "\n\n"
        snfMkImageScriptData += "snf-mkimage -a %s -t %s -u %s -r %s / | tee -a ~/snfmkimage.log" % (self.okeanosAuthURL,
                                                                                                     self.okeanosToken,
                                                                                                     newImageName,
                                                                                                     newImageName)
        snfMkImageScriptData += "\n"

        self.log("About to run %s" % snfMkImageScriptData)
        self.log("For %s@%s in order to create image %s" % (remoteUsername, ip, newImageName))
        exitCode, stdoutLines, stderrLines = runScriptDataOnHost(ip, snfMkImageScriptData, "slipstream-okeanos-build-image", username=remoteUsername)

        # localScriptFile = newTmpFileWithScriptData(snfMkImageScriptData)
        # remoteScriptFile = "slipstream-okeanos-build-image"
        # remoteCommand = "~/%s" % remoteScriptFile
        #
        # sftp = newSftpClient(ip, username=remoteUsername)
        # sftp.put(localScriptFile, remoteScriptFile)
        # sftp.close()
        # exitCode, stdoutLines, stderrLines = runCommandOnHost(ip, remoteCommand)

        return "YAHOO"  # FAKE

    def _start_image(self, userInfo, nodeInstance, vm_name):
        """
        :type userInfo: slipstream.UserInfo.UserInfo
        :type nodeInstance: slipstream.NodeInstance.NodeInstance
        :param vm_name: string
        :return: :raise Exception:
        """

        # userInfo = {
        # "okeanos.username": "UUID",
        #  "okeanos.max.iaas.workers": "20",
        #  "okeanos.quota.vm": "",
        #  "okeanos.service.name": "cyclades_compute",
        #  "General.On Error Run Forever": "true",
        #  "General.Timeout": "30",
        #  "General.On Success Run Forever": "true",
        #  "General.orchestrator.publicsshkey": "ssh-rsa LOCALKEY root@snf-000000\n",
        #  "okeanos.orchestrator.instance.type": "C2R2048D10ext_vlmc",
        #  "okeanos.orchestrator.imageid": "fe31fced-a3cf-49c6-b43b-f58f5235ba45",
        #  "User.email": "super@sixsq.com",
        #  "General.default.cloud.service": "okeanos",
        #  "okeanos.endpoint": "https://accounts.okeanos.grnet.gr/identity/v2.0",
        #  "User.lastName": "User",
        #  "okeanos.update.clienturl": "https://SlipStreamServer/downloads/okeanoslibs.tar.gz",
        #  "User.firstName": "Super",
        #  "okeanos.service.region": "default",
        #  "General.ssh.public.key": "ssh-rsa SlipStreamServerUIUserSSHKey\n",
        #  "okeanos.service.type": "compute",
        #  "General.Verbosity Level": "3",
        #  "okeanos.password": "TOKEN"
        #}

        # nodeInstance = NodeInstance({
        #  "image.parentUri": "module/P5",
        #  "image.shortName": "B3",
        #  "image.logoLink": "",
        #  "abort": None,
        #  "image.deleted": "false",
        #  "image.category": "Image",
        #  "image.class": "com.sixsq.slipstream.persistence.ImageModule",
        #  "image.version": "8",
        #  "okeanos.security.groups": "default",
        #  "okeanos.instance.type": "C2R2048D10ext_vlmc",
        #  "extra.disk.volatile": None,
        #  "image.platform": "ubuntu",
        #  "network": "Public",
        #  "image.moduleReferenceUri": "module/P5/I5",
        #  "hostname": None,
        #  "image.lastModified": "2014-09-20 17:56:10.860 EEST",
        #  "is.orchestrator": "false",
        #  "url.service": None,
        #  "statecustom": None,
        #  "image.isBase": "false",
        #  "complete": "false",
        #  "image.resourceUri": "module/P5/B3/8",
        #  "image.id": "fe31fced-a3cf-49c6-b43b-f58f5235ba45",
        #  "image.loginUser": "root",
        #  "image.isLatestVersion": "true",
        #  "scale.state": "creating",
        #  "image.packages": [],
        #  "image.name": "P5/B3",
        #  "name": "machine",
        #  "instanceid": None,
        #  "cloudservice": "okeanos",
        #  "image.recipe": "#!/bin/sh\n\necho BuildImage > /root/BuildImage.txt\n\n",
        #  "url.ssh": None,
        #  "image.creation": "2014-09-20 17:56:10.822 EEST",
        #  "image.prerecipe": "",
        #  "vmstate": "Unknown",
        #  "image.description": ""
        #})

        self.log()
        self.log("userInfo = %s" % userInfo)
        self.log("nodeInstance = %s" % nodeInstance)
        self.log("vm_name = %s" % vm_name)
        initScriptData = self._get_init_script(nodeInstance)
        self.log("initScriptData = %s" % initScriptData)

        imageId = nodeInstance.get_image_id()
        flavorIdOrName = nodeInstance.get_instance_type()
        sshPubKey = userInfo.get_public_keys()
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
            runInitScriptSynchronously=runInitScriptSynchronously,
            projectId=self.okeanosProjectId)
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
        # 'multiplicity': 1,
        # 'image': {
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
        if isinstance(vm, ListNodeResult):
            return vm.id
        else:
            return vm['id']

    def _vm_get_state(self, vm):
        if isinstance(vm, ListNodeResult):
            return vm.status
        else:
            return vm['status']

    def _wait_and_get_instance_ip_address(self, vm):
        # vm =
        # {
        # 'ip': '',
        # 'instance': <slipstream.cloudconnectors.okeanos.NodeDetails object at 0x0000000>,
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

    def list_instances(self):
        return self.okeanosClient.listNodes()

    def _get_bootstrap_script(self, node_instance, pre_bootstrap=None,
                              post_bootstrap=None, username=None, **kwargs):
        _pre_export = 'pip uninstall -y kamaki || true'
        _pre_export += '\npip uninstall -y kamaki || true'
        _pre_export += '\nssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa < /dev/null || true'
        return super(OkeanosClientCloud, self)._get_bootstrap_script(
            node_instance, pre_export=_pre_export, pre_bootstrap=pre_bootstrap,
            post_bootstrap=post_bootstrap, username=username)
