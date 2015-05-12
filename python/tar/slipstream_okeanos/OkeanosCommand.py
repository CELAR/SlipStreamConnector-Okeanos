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
from slipstream_okeanos.OkeanosClientCloud import OkeanosClientCloud


class OkeanosCommand(CloudClientCommand):

    ENDPOINT_KEY = 'endpoint'
    ENDPOINT_DEFAULT = 'https://accounts.okeanos.grnet.gr/identity/v2.0'
    PROJECT_ID_KEY = 'project-id'

    def __init__(self, args=None):
        super(OkeanosCommand, self).__init__()

    def get_connector_class(self):
        return OkeanosClientCloud

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
