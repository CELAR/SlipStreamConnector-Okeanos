# This is a helper script for development purposes.

from os import environ as ENV
from kamaki.clients.astakos import AstakosClient
from kamaki.clients.cyclades import CycladesClient, CycladesBlockStorageClient
from kamaki.clients.utils import https
from slipstream_okeanos import OkeanosNativeClient

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
    return response

def deleteVolume(volumeId):
    response = bsc.delete_volume(volumeId)
    return response

def listVolumes(details=True):
    """
    :param details: boolean
    :return:
    """
    response = bsc.list_volumes(details)
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
        return {}
    volumeId = volumeOpt['id']
    response = deleteVolume(volumeId)
    return response
