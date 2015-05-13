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

import java.util.HashMap;
import java.util.Map;
import java.util.logging.Logger;

import com.sixsq.slipstream.configuration.Configuration;
import com.sixsq.slipstream.connector.CliConnectorBase;
import com.sixsq.slipstream.connector.Connector;
import com.sixsq.slipstream.credentials.Credentials;
import com.sixsq.slipstream.exceptions.ConfigurationException;
import com.sixsq.slipstream.exceptions.InvalidElementException;
import com.sixsq.slipstream.exceptions.SlipStreamRuntimeException;
import com.sixsq.slipstream.exceptions.ValidationException;
import com.sixsq.slipstream.persistence.ImageModule;
import com.sixsq.slipstream.persistence.ModuleParameter;
import com.sixsq.slipstream.persistence.Run;
import com.sixsq.slipstream.persistence.ServiceConfigurationParameter;
import com.sixsq.slipstream.persistence.User;
import com.sixsq.slipstream.persistence.UserParameter;

public class OkeanosConnector extends CliConnectorBase {
    public static final String ClassName = OkeanosConnector.class.getName();
    private static Logger log = Logger.getLogger(ClassName);

    public static final String CLOUD_SERVICE_NAME = "okeanos";
    public static final String CLOUDCONNECTOR_PYTHON_MODULENAME = "slipstream_okeanos.OkeanosClientCloud";

    public OkeanosConnector() { this(OkeanosConnector.CLOUD_SERVICE_NAME); }

    public OkeanosConnector(String instanceName) { super(instanceName); }

    @Override
    public Map<String, ServiceConfigurationParameter> getServiceConfigurationParametersTemplate()
    		throws ValidationException {
        return new OkeanosSystemConfigurationParametersFactory(getConnectorInstanceName()).getParameters();
    }

    @Override
    public Map<String, ModuleParameter> getImageParametersTemplate() throws ValidationException {
        return new OkeanosImageParametersFactory(getConnectorInstanceName()).getParameters();
    }

    public Connector copy() { return new OkeanosConnector(getConnectorInstanceName()); }

    public String getCloudServiceName() { return OkeanosConnector.CLOUD_SERVICE_NAME; }

    @Override
    protected String getCloudConnectorPythonModule() {
    	return CLOUDCONNECTOR_PYTHON_MODULENAME;
    }

    @Override
    protected Map<String, String> getConnectorSpecificUserParams(User user) throws ConfigurationException, ValidationException {
        Map<String, String> userParams = new HashMap<String, String>();
        userParams.put("endpoint", getEndpoint(user));
        String projectId = getProjectID(user);
        if (!projectId.isEmpty()) {
        	userParams.put("project-id", projectId);
        }
        return userParams;
    }

    @Override
    protected Map<String, String> getConnectorSpecificLaunchParams(Run run, User user) throws ConfigurationException, ValidationException {
    	Map<String, String> launchParams = new HashMap<String, String>();
    	launchParams.put("instance-type", getInstanceType(run));
    	launchParams.put("security-groups", getSecurityGroups(run));
    	return launchParams;
    }

    protected void validateDescribe(User user) throws ValidationException {
		this.validateDescribe(user);
		validateBaseParameters(user);
	}

    protected void validateTerminate(Run run, User user) throws ValidationException {
		this.validateTerminate(run, user);
		validateBaseParameters(user);
	}

    protected void validateLaunch(Run run, User user) throws ValidationException{
		super.validateLaunch(run, user);
		validateBaseParameters(user);
		validateLaunchParams(run, user);
	}

    private void validateBaseParameters(User user) throws ValidationException {
		if (isEmptyOrNull(getEndpoint(user))) {
			throw (new ValidationException("Cloud Endpoint cannot be empty. Please contact your SlipStream administrator."));
		}
	}

	private void validateLaunchParams(Run run, User user) throws ValidationException {
        final String instanceType = getInstanceType(run);
        if(isEmptyOrNull(instanceType)) {
            throw new ValidationException("Instance type (flavor) cannot be empty");
        }
        final String imageId = getImageId(run, user);
        if (isEmptyOrNull(imageId)){
            throw new ValidationException("Image ID cannot be empty");
        }
    }

    @Override
    protected String getKey(User user) {
        try {
            return getCredentials(user).getKey();
        }
        catch(InvalidElementException e) {
            throw new SlipStreamRuntimeException(e);
        }
    }

    @Override
    protected String getSecret(User user) {
        try {
            return getCredentials(user).getSecret();
        }
        catch(InvalidElementException e) {
            throw new SlipStreamRuntimeException(e);
        }
    }

    private String getInstanceType(Run run) throws ValidationException {
	    return isInOrchestrationContext(run) ?
	    	getOrchestratorInstanceType() : getInstanceType(ImageModule.load(run.getModuleResourceUrl()));
	}

    private String getProjectID(User user) throws ValidationException {
		return user.getParameterValue(constructKey(OkeanosUserParametersFactory.PROJECT_ID_PARAMETER_NAME), "");
	}

	private String getOrchestratorInstanceType() throws ValidationException {
		return Configuration.getInstance().getRequiredProperty(
		        constructKey(OkeanosUserParametersFactory.ORCHESTRATOR_INSTANCE_TYPE_PARAMETER_NAME));
	}

	private String getSecurityGroups(Run run) throws ValidationException {
        return isInOrchestrationContext(run)
            ? "default"
            : getParameterValue(OkeanosImageParametersFactory.SECURITY_GROUPS,ImageModule.load(run.getModuleResourceUrl()));
    }

    @Override
    public Credentials getCredentials(User user) {
        return new OkeanosCredentials(user, getConnectorInstanceName());
    }

    @Override
    public Map<String, UserParameter> getUserParametersTemplate() throws ValidationException {
        return new OkeanosUserParametersFactory(getConnectorInstanceName()).getParameters();
    }

	@Override
	protected String constructKey(String key) throws ValidationException {
	    return new OkeanosUserParametersFactory(getConnectorInstanceName()).constructKey(key);
	}

	private boolean isEmptyOrNull(String s) { return s == null || s.isEmpty(); }
}
