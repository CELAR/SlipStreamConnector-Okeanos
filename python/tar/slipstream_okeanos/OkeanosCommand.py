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

from optparse import OptionParser
import os

from slipstream.SlipStreamHttpClient import UserInfo
from sliplstream_okeanos import OkeanosNativeClient
from sliplstream_okeanos.OkeanosClientCloud import OkeanosClientCloud


class OkeanosCommand(object):
    def __init__(self, args=None):
        self.providerName = OkeanosClientCloud.cloudName
        self.parser, self.options, self.args = self.parseArgs(args)
        self.userInfo = self._createUserInfo()

        token = self.options.secret
        authURL = self.options.endpoint
        self.okeanosClient = OkeanosNativeClient(token, authURL)

    def parseArgs(self, args=None):
        parser = OptionParser()
        self.setCommonOptions(parser)
        self.setExtraOptions(parser)
        options, args = parser.parse_args(args)
        self.checkCommonOptions(options, parser)
        self.checkExtraOption(options, parser)
        return parser, options, args

    def setCommonOptions(self, parser):
        parser.add_option('--username', dest='key', help='Key', default='', metavar='KEY')

        parser.add_option('--password', dest='secret', help='Secret', default='', metavar='SECRET')

        parser.add_option('--endpoint', dest='endpoint',
                          help='Identity service (Astakos, default: https://accounts.okeanos.grnet.gr/identity/v2.0)',
                          default='https://accounts.okeanos.grnet.gr/identity/v2.0', metavar='ENDPOINT')

        parser.add_option('--region', dest='region',
                          help='Region (default: default)',
                          default='default', metavar='REGION')

        parser.add_option('--service-type', dest='service_type',
                          help='Type-name of the service which provides the instances functionality (default: compute)',
                          default='compute', metavar='TYPE')

        parser.add_option('--service-name', dest='service_name',
                          help='Name of the service which provides the instances functionality (default: cyclades_compute)',
                          default='cyclades_compute', metavar='NAME')

        parser.add_option('--project', dest='project', help='Project (Tenant)', default='', metavar='PROJECT')


    def _createUserInfo(self):
        if not self.providerName:
            raise Exception('providerName has to be set for %s' % self.__class__)
        os.environ['SLIPSTREAM_CONNECTOR_INSTANCE'] = self.providerName

        userInfo = UserInfo(self.providerName)
        self.setCommonUserInfo(userInfo)
        self.setExtraUserInfo(userInfo)

        return userInfo

    def checkCommonOptions(self, options, parser):
        if not all((options.key, options.secret, options.endpoint, options.region)):
            parser.error('Some mandatory options were not given values.')

    def setCommonUserInfo(self, userInfo):
        userInfo[self.providerName + '.username'] = self.options.key
        userInfo[self.providerName + '.password'] = self.options.secret
        userInfo[self.providerName + '.endpoint'] = self.options.endpoint
        userInfo[self.providerName + '.service.type'] = self.options.service_type
        userInfo[self.providerName + '.service.name'] = self.options.service_name
        userInfo[self.providerName + '.service.region'] = self.options.region
        userInfo[self.providerName + '.tenant.name'] = self.options.project or self.options.key

    def checkExtraOption(self, options, parser):
        pass

    def setExtraOptions(self, parser):
        pass

    def setExtraUserInfo(self, userInfo):
        pass

    def doWork(self):
        pass



