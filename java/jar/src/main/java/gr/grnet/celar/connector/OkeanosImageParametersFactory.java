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

import com.sixsq.slipstream.exceptions.ValidationException;
import com.sixsq.slipstream.factory.ModuleParametersFactoryBase;
import com.sixsq.slipstream.persistence.ImageModule;

public class OkeanosImageParametersFactory extends ModuleParametersFactoryBase {

    public static final String SECURITY_GROUPS = "security.groups";
	public OkeanosImageParametersFactory(String connectorInstanceName) throws ValidationException {
		super(connectorInstanceName);
	}

	@Override
	protected void initReferenceParameters() throws ValidationException {
		putMandatoryParameter(ImageModule.INSTANCE_TYPE_KEY, "Instance flavor", "");
        putMandatoryParameter(SECURITY_GROUPS, "Security Groups (comma separated list)", "default");
	}
}
