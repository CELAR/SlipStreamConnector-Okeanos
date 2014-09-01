package com.sixsq.slipstream.connector.okeanos;

import com.sixsq.slipstream.connector.AbstractDiscoverableConnectorService;

/**
 * @author Christos KK Loverdos <loverdos@gmail.com>
 */
public class OkeanosDiscoverableConnectorService extends AbstractDiscoverableConnectorService {
    public OkeanosDiscoverableConnectorService(String cloudServiceName) {
        super(cloudServiceName);
    }

    @Override
    public OkeanosConnector getInstance(String instanceName) {
        return new OkeanosConnector(instanceName);
    }
}
