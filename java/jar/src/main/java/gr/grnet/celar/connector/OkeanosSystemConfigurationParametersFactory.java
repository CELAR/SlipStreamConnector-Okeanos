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

import com.sixsq.slipstream.connector.SystemConfigurationParametersFactoryBase;
import com.sixsq.slipstream.connector.UserParametersFactoryBase;
import com.sixsq.slipstream.exceptions.ValidationException;

import java.util.logging.Logger;

import static java.lang.String.format;

public class OkeanosSystemConfigurationParametersFactory extends SystemConfigurationParametersFactoryBase {
	private static Logger log = Logger.getLogger(OkeanosSystemConfigurationParametersFactory.class.toString());

	public OkeanosSystemConfigurationParametersFactory(String connectorInstanceName)
			throws ValidationException {
		super(connectorInstanceName);
	}

    @Override
    protected void putMandatoryParameter(String name, String description, String value) throws ValidationException {
        log.info(
            format(
                "%s::putMandatoryParameter(), name=%s, description=%s, value=%s",
                OkeanosSystemConfigurationParametersFactory.class.getSimpleName(),
                name, description, value
            )
        );
        super.putMandatoryParameter(name, description, value);
    }

    @Override
    protected void putMandatoryEndpoint() throws ValidationException {
        putMandatoryParameter(
            super.constructKey(UserParametersFactoryBase.ENDPOINT_PARAMETER_NAME),
            "Service endpoint for " + getCategory(),
            "https://accounts.okeanos.grnet.gr/identity/v2.0"
        );
    }

    @Override
    protected void putMandatoryOrchestrationImageId() throws ValidationException {
        putMandatoryParameter(
            super.constructKey(UserParametersFactoryBase.ORCHESTRATOR_IMAGEID_PARAMETER_NAME),
            "Image Id of the orchestrator for " + getCategory(),
            "fe31fced-a3cf-49c6-b43b-f58f5235ba45"
        );
    }

    @Override
	protected void initReferenceParameters() throws ValidationException {

    	super.initReferenceParameters();
    	putMandatoryUpdateUrl();

    	log.entering(OkeanosSystemConfigurationParametersFactory.class.getSimpleName(), "initReferenceParameters");
        putMandatoryOrchestrationImageId();
		putMandatoryEndpoint();

		putMandatoryParameter(
            constructKey(OkeanosUserParametersFactory.ORCHESTRATOR_INSTANCE_TYPE_PARAMETER_NAME),
            "Okeanos flavor for the orchestrator. The actual image should support the desired Flavor",
            "C2R2048D10ext_vlmc"
        );

        putMandatoryParameter(
            constructKey(OkeanosUserParametersFactory.SERVICE_TYPE_PARAMETER_NAME),
            "Type-name of the service which provides the instances functionality",
            "compute"
        );

        putMandatoryParameter(
            constructKey(OkeanosUserParametersFactory.SERVICE_NAME_PARAMETER_NAME),
            "Name of the service which provides the instances functionality",
            "cyclades_compute"
        );

        putMandatoryParameter(
            constructKey(OkeanosUserParametersFactory.SERVICE_REGION_PARAMETER_NAME),
            "Region used by this cloud connector", "default"
        );
	}

}
