from slipstream.command.RunInstancesCommand import RunInstancesCommand
from slipstream_okeanos.OkeanosCommand import OkeanosCommand


class OkeanosRunInstances(RunInstancesCommand, OkeanosCommand):

    INSTANCE_TYPE_KEY = 'instance-type'
    SECURITY_GROUP_KEY = 'security-groups'

    def __init__(self):
        super(OkeanosRunInstances, self).__init__()

    def set_cloud_specific_options(self, parser):
        OkeanosCommand.set_cloud_specific_options(self, parser)

        self.parser.add_option('--' + self.INSTANCE_TYPE_KEY, dest=self.INSTANCE_TYPE_KEY,
                               help='Instance type (flavour).',
                               default='', metavar='FLAVOUR')

        self.parser.add_option('--' + self.SECURITY_GROUP_KEY, dest=self.SECURITY_GROUP_KEY,
                               help='Security groups. Comma separated list. (Default: default)',
                               default='default', metavar='FLAVOUR')

    def get_cloud_specific_node_inst_cloud_params(self):
        return {'instance.type': self.get_option(self.INSTANCE_TYPE_KEY),
                'security.groups': self.get_option(self.SECURITY_GROUP_KEY)}

    def get_cloud_specific_mandatory_options(self):
        return OkeanosCommand.get_cloud_specific_mandatory_options(self) + \
            [self.INSTANCE_TYPE_KEY]
