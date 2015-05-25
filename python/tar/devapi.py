# This is a helper script for development purposes.

from os import environ as ENV
from kamaki.clients.astakos import AstakosClient
from kamaki.clients.cyclades import CycladesClient, CycladesBlockStorageClient
from kamaki.clients.utils import https

authURL = "https://accounts.okeanos.grnet.gr/identity/v2.0"
X_AUTH_TOKEN_NAME = 'X_AUTH_TOKEN'
token = ENV[X_AUTH_TOKEN_NAME]

https.patch_ignore_ssl()

cycladesServiceType = CycladesClient.service_type
blockStorageServiceType = CycladesBlockStorageClient.service_type

astakosClient = AstakosClient(authURL, token)
cycladesURL = astakosClient.get_endpoint_url(cycladesServiceType)
print "cycladesURL = %s" % cycladesURL
blockStorageURL = astakosClient.get_endpoint_url(blockStorageServiceType)
print "blockStorageURL = %s" % blockStorageURL
cycladesClient = CycladesClient(cycladesURL, token)
blockStorageClient = CycladesBlockStorageClient(blockStorageURL, token)

# servers = cycladesClient.list_servers()
# flavors = cycladesClient.list_flavors()
#
#
def printEndpoints():
    for endpoint in astakosClient.get_endpoints()['access']['serviceCatalog']:
        print endpoint['type']
#
#
# # grab the first server
# def serverId():
#     return cycladesClient.list_servers()[0][u'id']


def createVolume(sizeGB, serverId, name):
    volumeContainer = blockStorageClient.create_volume(sizeGB, serverId, name)
    volume = volumeContainer[u'volume']
    volumeId = volume[u'id']
    return volumeId
#
#
# def deleteVolume(volumeId):
#     response = blockStorageClient.delete_volume(volumeId)
#     return response
#
#
# def listVolumes():
#     return blockStorageClient.list_volumes()
