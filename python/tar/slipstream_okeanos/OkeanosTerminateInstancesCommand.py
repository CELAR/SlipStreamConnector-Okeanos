from slipstream.command.TerminateInstancesCommand import TerminateInstancesCommand
from slipstream_okeanos.OkeanosCommand import OkeanosCommand


class OkeanosTerminateInstances(TerminateInstancesCommand, OkeanosCommand):

    def __init__(self):
        super(OkeanosTerminateInstances, self).__init__()
