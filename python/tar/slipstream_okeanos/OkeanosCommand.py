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

from slipstream.command.CloudClientCommand import CloudClientCommand
from slipstream.UserInfo import UserInfo
from slipstream_okeanos.OkeanosClientCloud import OkeanosClientCloud
from slipstream import util
from os import environ as ENV
import inspect
from . import LOG


class OkeanosCommand(CloudClientCommand):

    ENDPOINT_KEY = 'endpoint'
    ENDPOINT_DEFAULT = 'https://accounts.okeanos.grnet.gr/identity/v2.0'
    PROJECT_ID_KEY = 'project-id'

    def __init__(self, args=None):
        super(OkeanosCommand, self).__init__()
        key = util.ENV_CONNECTOR_INSTANCE
        # This is not set if you try to call the okeanos-*-instances scripts
        # directly on the command line.
        if key not in ENV:
            ENV[key] = self.get_connector_class().cloudName

    def get_connector_class(self):
        return OkeanosClientCloud

    def _parse_args(self):
        self._parse()
        # For convenience from the command line, we inject the password (token)
        # if we can get it from the environment
        passwd_key = UserInfo.CLOUD_PASSWORD_KEY
        if getattr(self.options, passwd_key, None) is None:
            x_auth_token_name = 'X_AUTH_TOKEN'
            if x_auth_token_name in ENV:
                self.log('%s has been set in the environment' % x_auth_token_name)
                x_auth_token = ENV[x_auth_token_name]
                setattr(self.options, passwd_key, x_auth_token)

        self._check_options()

    def _get_common_mandatory_options(self):
        # username is not needed at all for ~okeanos; the password (token) is enough for the API calls.
        return [UserInfo.CLOUD_PASSWORD_KEY]

    def set_cloud_specific_options(self, parser):
        parser.add_option('--' + self.ENDPOINT_KEY, dest=self.ENDPOINT_KEY,
                          help='Cloud endpoint. (Default: %s)' % self.ENDPOINT_DEFAULT,
                          default=self.ENDPOINT_DEFAULT, metavar='ENDPOINT')

        parser.add_option('--' + self.PROJECT_ID_KEY, dest=self.PROJECT_ID_KEY,
                          help='ID of the project that provides the resources.',
                          default=None, metavar='PROJECTID')

    def get_cloud_specific_user_cloud_params(self):
        return {'project.id': self.get_option(self.PROJECT_ID_KEY),
                self.ENDPOINT_KEY: self.get_option(self.ENDPOINT_KEY)}

    def log(self, msg=''):
        who = '%s::%s' % (self.__class__.__name__, inspect.stack()[1][3])
        LOG('%s# %s' % (who, msg))
