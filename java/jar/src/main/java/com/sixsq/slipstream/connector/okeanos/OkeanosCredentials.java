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

package com.sixsq.slipstream.connector.okeanos;

import com.sixsq.slipstream.connector.CredentialsBase;
import com.sixsq.slipstream.credentials.Credentials;
import com.sixsq.slipstream.exceptions.InvalidElementException;
import com.sixsq.slipstream.exceptions.SlipStreamRuntimeException;
import com.sixsq.slipstream.exceptions.ValidationException;
import com.sixsq.slipstream.persistence.User;

import java.util.logging.Level;
import java.util.logging.Logger;

public class OkeanosCredentials extends CredentialsBase implements Credentials {
    private static Logger log = Logger.getLogger(OkeanosCredentials.class.toString());
    public OkeanosCredentials(User user, String connectorInstanceName) {
        super(user);
        try {
            cloudParametersFactory = new OkeanosUserParametersFactory(connectorInstanceName);
        } catch (ValidationException e) {
            log.log(Level.SEVERE, "Creating cloudParametersFactory", e);
            throw new SlipStreamRuntimeException(e);
        }
    }

    public String getKey() throws InvalidElementException {
        return getParameterValue(OkeanosUserParametersFactory.KEY_PARAMETER_NAME);
    }

    public String getSecret() throws InvalidElementException {
        return getParameterValue(OkeanosUserParametersFactory.SECRET_PARAMETER_NAME);
    }

}
