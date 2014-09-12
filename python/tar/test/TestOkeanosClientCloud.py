import os
import unittest

from slipstream_okeanos.OkeanosClientCloud import OkeanosClientCloud
from slipstream.ConfigHolder import ConfigHolder
from slipstream.NodeDecorator import (RUN_CATEGORY_DEPLOYMENT,
                                      KEY_RUN_CATEGORY)


class TestOkeanosClientCloud(unittest.TestCase):

    def setUp(self):
        os.environ['SLIPSTREAM_CONNECTOR_INSTANCE'] = 'Test'
        self.ch = ConfigHolder(config={'foo': 'bar'}, context={'foo': 'bar'})
        self.ch.set(KEY_RUN_CATEGORY, RUN_CATEGORY_DEPLOYMENT)

    def test_OkeanosClientCloudInit(self):
        okeanos = OkeanosClientCloud(self.ch)
        assert okeanos
        assert okeanos.run_category == RUN_CATEGORY_DEPLOYMENT
