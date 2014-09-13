package com.sixsq.slipstream.connector.okeanos;

import com.sixsq.slipstream.connector.AbstractDiscoverableConnectorService;

/**
 * @author Christos KK Loverdos <loverdos@gmail.com>
 */
public class OkeanosDiscoverableConnectorService extends AbstractDiscoverableConnectorService {

	public OkeanosDiscoverableConnectorService() {
		super(OkeanosConnector.CLOUD_SERVICE_NAME);
    }

    @Override
    public OkeanosConnector getInstance(String instanceName) {
        return new OkeanosConnector(instanceName);
    }
}
