from slipstream.command.DescribeInstancesCommand import DescribeInstancesCommand
from slipstream_okeanos.OkeanosCommand import OkeanosCommand


class OkeanosDescribeInstances(DescribeInstancesCommand, OkeanosCommand):

    def __init__(self):
        super(OkeanosDescribeInstances, self).__init__()

    def _vm_get_state(self, cc, vm):
        return cc._vm_get_state(vm)

