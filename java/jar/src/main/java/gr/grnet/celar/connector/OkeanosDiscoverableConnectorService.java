/*
 * Copyright (c) 2014 GRNET SA (grnet.gr)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package gr.grnet.celar.connector;

import com.sixsq.slipstream.connector.AbstractDiscoverableConnectorService;

public class OkeanosDiscoverableConnectorService extends AbstractDiscoverableConnectorService {

	public OkeanosDiscoverableConnectorService() {
		super(OkeanosConnector.CLOUD_SERVICE_NAME);
    }

    @Override
    public OkeanosConnector getInstance(String instanceName) {
        return new OkeanosConnector(instanceName);
    }
}
