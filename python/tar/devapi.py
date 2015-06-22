# This is a helper script for development purposes.

from os import environ as ENV
from kamaki.clients.astakos import AstakosClient
from kamaki.clients.cyclades import CycladesClient, CycladesBlockStorageClient
from kamaki.clients.utils import https
from slipstream_okeanos import OkeanosNativeClient
from slipstream_okeanos import runCommandOnHost

https.patch_ignore_ssl()

authURL = "https://accounts.okeanos.grnet.gr/identity/v2.0"
X_AUTH_TOKEN_NAME = 'X_AUTH_TOKEN'
token = ENV[X_AUTH_TOKEN_NAME]

projectId = '464eb0e7-b556-4fc7-8afb-d590feebaad8'
serverId = '660580'

cycladesServiceType = CycladesClient.service_type
blockStorageServiceType = CycladesBlockStorageClient.service_type

ac = AstakosClient(authURL, token)

cycladesURL = ac.get_endpoint_url(cycladesServiceType)
cc = CycladesClient(cycladesURL, token)

blockStorageURL = ac.get_endpoint_url(blockStorageServiceType)
bsc = CycladesBlockStorageClient(blockStorageURL, token)

onc = OkeanosNativeClient(token, authURL)

print "cycladesURL = %s" % cycladesURL
print "blockStorageURL = %s" % blockStorageURL
print "ac = %s" % ac
print "cc = %s" % cc
print "bsc = %s" % bsc
print "onc = %s" % onc

# servers = cc.list_servers()
# flavors = cc.list_flavors()

def printEndpoints():
    for endpoint in ac.get_endpoints()['access']['serviceCatalog']:
        print endpoint['type']


def createVolume(sizeGB, name, serverId=serverId, projectId=projectId):
    response = bsc.create_volume(sizeGB, server_id=serverId, display_name=name, project=projectId)

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

    return response

def deleteVolume(volumeId):
    response = bsc.delete_volume(volumeId)

    # response is something like this (the HTTP response headers directly)
    # {
    #     'content-length': '0',
    #     'content-language': 'en-us',
    #     'expires': 'Tue, 16 Jun 2015 11:59:05 GMT',
    #     'vary': 'X-Auth-Token, Accept-Language',
    #     'server': 'nginx/1.2.1',
    #     'last-modified': 'Tue, 16 Jun 2015 11:59:05 GMT',
    #     'connection': 'keep-alive',
    #     'cache-control': 'no-cache, no-store, must-revalidate, max-age=0',
    #     'date': 'Tue, 16 Jun 2015 11:59:05 GMT',
    #     'content-type': 'application/json; charset=UTF-8'
    # }

    return response

def listVolumes(details=True):
    """
    :param details: boolean
    :return:
    """
    response = bsc.list_volumes(details)

    # response is an array of these
    # {
    #     u'status': u'in_use',
    #     u'user_id': u'fc95f201-d5a9-46fa-8ede-b8983b420a40',
    #     u'attachments': [
    #         {
    #             u'server_id': 587337,
    #             u'device_index': 0,
    #             u'volume_id': 987
    #         }
    #     ],
    #     u'links': [
    #         {
    #             u'href': u'https://cyclades.okeanos.grnet.gr/volume/v2.0/volumes/987',
    #             u'rel': u'self'
    #         }, {
    #             u'href': u'https://cyclades.okeanos.grnet.gr/volume/v2.0/volumes/987',
    #             u'rel': u'bookmark'
    #         }
    #     ],
    #     u'deleted': False,
    #     u'tenant_id': u'464eb0e7-b556-4fc7-8afb-d590feebaad8',
    #     u'created_at': u'2014-11-17T08:49:15.539115+00:00',
    #     u'metadata': {},
    #     u'source_volid': None,
    #     u'delete_on_termination': True,
    #     u'image_id': None,
    #     u'volume_type': 1,
    #     u'snapshot_id': None,
    #     u'display_name': u'boot volume',
    #     u'display_description': u'boot volume',
    #     u'id': u'987',
    #     u'size': 20
    # }

    return response

def findVolumeByName(name):
    volumes = listVolumes()
    for volume in volumes:
        vname = volume['display_name']
        if vname == name:
            return volume
    return None

def deleteVolumeByName(name):
    volumeOpt = findVolumeByName(name)
    if volumeOpt is None:
        return None
    volumeId = volumeOpt['id']
    response = deleteVolume(volumeId)
    return response

def procPartitions(host):
    cmd = "/bin/bash -c 'cat /proc/partitions | sed 1d | sed /^\\$/d | awk \\'{print $4}\\''"
    print "cmd = %s" % cmd
    return runCommandOnHost(host, cmd)

def attachVolume(serverId=serverId, sizeGB=1, projectId=projectId):
    return onc.attachVolume(serverId, sizeGB, projectId)

def resizeServer(serverId=serverId, flavor='C2R2048D10drbd'):
    return onc.resizeNode(serverId, flavor)
