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

import com.sixsq.slipstream.connector.UserParametersFactoryBase;
import com.sixsq.slipstream.exceptions.ValidationException;

public class OkeanosUserParametersFactory extends UserParametersFactoryBase {
	public static final String PROJECT_ID_PARAMETER_NAME = "project.id";

	public OkeanosUserParametersFactory(String connectorInstanceName) throws ValidationException {
		super(connectorInstanceName);
	}

	@Override
	protected void initReferenceParameters() throws ValidationException {
		putMandatoryParameter(KEY_PARAMETER_NAME, "Okeanos UUID");
		putMandatoryPasswordParameter(SECRET_PARAMETER_NAME, "Okeanos Token");
		putParameter(PROJECT_ID_PARAMETER_NAME, "ID of the project that provides resources (optional)", false);
	}

}
