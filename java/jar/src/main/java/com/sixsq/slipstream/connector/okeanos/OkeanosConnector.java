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

import com.sixsq.slipstream.configuration.Configuration;
import com.sixsq.slipstream.connector.CliConnectorBase;
import com.sixsq.slipstream.connector.Connector;
import com.sixsq.slipstream.connector.ExecutionControlUserParametersFactory;
import com.sixsq.slipstream.connector.UserParametersFactoryBase;
import com.sixsq.slipstream.credentials.Credentials;
import com.sixsq.slipstream.exceptions.*;
import com.sixsq.slipstream.persistence.*;

import java.io.*;
import java.util.*;
import java.util.logging.Level;
import java.util.logging.Logger;

import static java.lang.String.format;

public class OkeanosConnector extends CliConnectorBase {
    public static final String ClassName = OkeanosConnector.class.getName();
    private static Logger log = Logger.getLogger(ClassName);
    public static final String CLOUD_SERVICE_NAME = "okeanos";
    public static final String CLOUDCONNECTOR_PYTHON_MODULENAME = "slipstream_okeanos.OkeanosClientCloud";

    public static final String COMMAND_DESCRIBE_INSTANCES  = format("%s/okeanos-describe-instances", CLI_LOCATION);
    public static final String COMMAND_RUN_INSTANCES       = format("%s/okeanos-run-instances", CLI_LOCATION);
    public static final String COMMAND_TERMINATE_INSTANCES = format("%s/okeanos-terminate-instances", CLI_LOCATION);

    public static final String BOOTSTRAP_PATH = "/tmp/slipstream.bootstrap";
    public static final String LOG_FILENAME = "orchestrator.slipstream.log";

    public OkeanosConnector() { this(OkeanosConnector.CLOUD_SERVICE_NAME); }

    public OkeanosConnector(String instanceName) { super(instanceName); }

    public boolean isEmptyOrNull(String s) { return s == null || s.isEmpty(); }

    public List<String> mkList(String... args) {
        final List<String> list = new ArrayList<>(args.length);
        list.addAll(Arrays.asList(args));
        return list;
    }

    public List<String> mkList(String command, List<String> others, String... more) {
        final List<String> list = new ArrayList<String>(1 + others.size() + more.length);
        list.add(command);
        list.addAll(others);
        list.addAll(mkList(more));
        return list;
    }

    public List<String> mkList(List<String> list, String ...more) {
        final List<String> bigOne = new ArrayList<String>(list);
        bigOne.addAll(mkList(more));
        return bigOne;
    }

    public List<String> mkList(String[] args, String ...more) {
        final List<String> bigOne = mkList(args);
        bigOne.addAll(mkList(more));
        return bigOne;
    }

    public String[] toArray(List<String> list) {
        return list.toArray(new String[list.size()]);
    }

    public String[] toArray(List<String> list, String ...more) {
        list.addAll(mkList(more));
        return list.toArray(new String[list.size()]);
    }

    public String[] toArray(String[] args, String ...more) {
        final List<String> list = mkList(args);
        return toArray(list, more);
    }

    protected String constructKey(String key) throws ValidationException {
        return new OkeanosUserParametersFactory(getConnectorInstanceName()).constructKey(key);
    }

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

    // instance type [slipstream] == flavor [~okeanos]
    protected String getInstanceType(Run run) throws SlipStreamClientException, ConfigurationException {
        final boolean inOrchestrationContext = isInOrchestrationContext(run);
        log.info("KK [okeanos::getInstanceType], inOrchestrationContext = " + inOrchestrationContext);
        log.info("KK [okeanos::getInstanceType], constructKey(" +OkeanosUserParametersFactory.ORCHESTRATOR_INSTANCE_TYPE_PARAMETER_NAME+ ") = " + constructKey(OkeanosUserParametersFactory.ORCHESTRATOR_INSTANCE_TYPE_PARAMETER_NAME));
        return inOrchestrationContext
            ? Configuration.
                getInstance().
                getRequiredProperty(
                    constructKey(OkeanosUserParametersFactory.ORCHESTRATOR_INSTANCE_TYPE_PARAMETER_NAME)
                )
            : getInstanceType(ImageModule.load(run.getModuleResourceUrl()));
    }

    private void validateRun(Run run, User user) throws ConfigurationException, SlipStreamClientException, ServerExecutionEnginePluginException {
        final String instanceType = getInstanceType(run);
        if(isEmptyOrNull(instanceType)) {
            throw new ValidationException("Instance type (flavor) cannot be empty");
        }
        final String imageId = getImageId(run, user);
        if (isEmptyOrNull(imageId)){
            throw new ValidationException("Image ID cannot be empty");
        }
    }

    protected void validateCredentials(User user) throws ValidationException {
        super.validateCredentials(user);

        final String endpoint = getEndpoint(user);
        if (isEmptyOrNull(endpoint)) {
            throw new ValidationException("Cloud Endpoint cannot be empty. Please contact your SlipStream administrator.");
        }
    }

    protected String getRegion() throws ConfigurationException, ValidationException {
        return Configuration.
            getInstance().
            getRequiredProperty(
                constructKey(OkeanosUserParametersFactory.SERVICE_REGION_PARAMETER_NAME)
            );
    }

    protected String getServiceType() throws ConfigurationException, ValidationException {
        return Configuration.
            getInstance().
            getRequiredProperty(
                constructKey(OkeanosUserParametersFactory.SERVICE_TYPE_PARAMETER_NAME)
            );
    }

    protected String getServiceName() throws ConfigurationException, ValidationException {
        return Configuration.
            getInstance().
            getRequiredProperty(
                constructKey(OkeanosUserParametersFactory.SERVICE_NAME_PARAMETER_NAME)
            );
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

    @Override
    protected String getEndpoint(User user) {
        return user.
            getParameter(
                getConnectorInstanceName() + "." + UserParametersFactoryBase.ENDPOINT_PARAMETER_NAME
            ).getValue();
    }

    static final class ExtraDisk {
        final String name;
        final String value;

        static ExtraDisk None = new ExtraDisk();

        ExtraDisk(String name, String value) {
            if(name == null) {
                throw new NullPointerException("null name for extra disk");
            }
            this.name = name;
            if(value == null || value.trim().length() == 0) {
                this.value = "0";
            }
            else {
                this.value = value;
            }
        }

        private ExtraDisk() {
            this.name = null;
            this.value = null;
        }

        boolean isNone() { return this.name == null; }

        @Override
        public boolean equals(Object o) {
            if(this == o) {
                return true;
            }
            if(o == null || getClass() != o.getClass()) {
                return false;
            }

            ExtraDisk extraDisk = (ExtraDisk) o;

            if(name != null ? !name.equals(extraDisk.name) : extraDisk.name != null) {
                return false;
            }
            if(value != null ? !value.equals(extraDisk.value) : extraDisk.value != null) {
                return false;
            }

            return true;
        }

        @Override
        public int hashCode() {
            int result = name != null ? name.hashCode() : 0;
            result = 31 * result + (value != null ? value.hashCode() : 0);
            return result;
        }

        @Override
        public String toString() {
            if(isNone()) {
                return "ExtraDisk(<None>)";
            } else {
                final StringBuilder sb = new StringBuilder("ExtraDisk(");
                sb.append("'").append(name).append('\'');
                sb.append(", '").append(value).append('\'');
                sb.append(')');
                return sb.toString();
            }
        }
    }

    private String getVolatileDiskSize(Run run) throws NotFoundException, AbortException {
        switch(run.getType()) {
            case Machine:
                final String extraDiskName = Run.MACHINE_NAME_PREFIX + ImageModule.EXTRADISK_PARAM_PREFIX + ".volatile";
                final String extraDiskValue = run.getRuntimeParameterValue(extraDiskName);
                
                return extraDiskValue;
            default:
                return null; // WAT ???
        }
    }

    private List<String> getCommonParams(User user) throws ValidationException {
        return mkList(
            "--username", getKey(user),
            "--password", getSecret(user),
            "--endpoint", getEndpoint(user),
            "--region", getRegion(),
            "--service-type", getServiceType(),
            "--service-name", getServiceName()
        );
    }

    protected String getVmName(Run run) {
        return run.getType() == RunType.Orchestration
            ? getOrchestratorName(run) + "-" + run.getUser() + "-" + run.getUuid()
            : "machine" + "-" + run.getUser() + "-" + run.getUuid();
    }

    protected String getNetwork(Run run) throws ValidationException{
        if (run.getType() == RunType.Orchestration) {
            return "";
        } else {
            ImageModule machine = ImageModule.load(run.getModuleResourceUrl());
            return machine.getParameterValue(ImageModule.NETWORK_KEY, null);
        }
    }

    protected String getSecurityGroups(Run run) throws ValidationException {
        return isInOrchestrationContext(run)
            ? "default"
            : getParameterValue(
                OkeanosImageParametersFactory.SECURITY_GROUPS,
                ImageModule.load(run.getModuleResourceUrl()));
    }

    class Script {
        final StringBuilder text = new StringBuilder();
        final String logdir;
        final String logfilename;
        final String logfilepath;

        Script(String logdir, String logfilename) {
            this.logdir = logdir;
            this.logfilename = logfilename;
            this.logfilepath = logdir + "/" + logfilename;
        }

        Script similar() {
            return new Script(this.logdir, this.logfilename);
        }

        private Script addnl(String line) {
            text.append(line).append("\n");
            return this;
        }

        Script comment(String comment) {
            addnl(format("# %s", comment));
            return this;
        }

        Script export(String name, String value) {
            addnl(format("export %s=\"%s\"", name, value));
            return this;
        }

        Script nl() {
            return addnl("");
        }

        Script command(String ...args) {
            final StringBuilder sb = new StringBuilder();

            for(int i = 0; i < args.length; i++) {
                final String arg = args[i];
                if(arg.trim().isEmpty()) {
                    sb.append('"');
                    sb.append(arg);
                    sb.append('"');
                }
                else {
                    sb.append(arg);
                }
                if(i < args.length) { sb.append(' '); }
            }

            return addnl(sb.toString());
        }

        Script hashbang(String hb) {
            return addnl("#!" + hb);
        }

        Script log(String... args) {
            final String[] array = {"echo", "INFO", "'['`date`']'",};
            final List<String> list = mkList(array, args);
            final String[] newArgs = toArray(list);
            return command(newArgs);
        }

        Script logBegin(String ...args) {
            final String[] array = {"BEGIN",};
            final List<String> list = mkList(array, args);
            final String[] newArgs = toArray(list, "|", "tee", "-a", logfilepath);
            return log(newArgs);
        }

        Script logEnd(String ...args) {
            final String[] array = {"END  ",};
            final List<String> list = mkList(array, args);
            final String[] newArgs = toArray(list, "|", "tee", "-a", logfilepath);
            return log(newArgs);
        }

        // command with logging
        Script commandL(String ...commandArgs) {
            final List<String> enhancedList  = mkList(commandArgs, "2>&1", "|", "tee", "-a", logfilepath);
            final String[] enhancedArgs = toArray(enhancedList);
            command(enhancedArgs);

            return this;
        }

        Script include(Script other) {
            return addnl(other.toString());
        }

        Script includeIf(boolean condition, Script onTrue, Script onFalse) {
            if(condition) {
                return include(onTrue);
            }
            else {
                return include(onFalse);
            }
        }

        @Override
        public String toString() { return text.toString(); }
    }

    @Override
    protected String getCookieForEnvironmentVariable(String identifier, String runId) {
        return generateCookie(identifier, runId);
    }

    protected String createContextualizationData(Run run, User user) throws ConfigurationException, ServerExecutionEnginePluginException, SlipStreamClientException {

        final Configuration configuration = Configuration.getInstance();

        final String username = user.getName();

        final String[] bootstrapCmdline;
        final String nodename;
        final boolean inOrchestrationContext = isInOrchestrationContext(run);
        if(inOrchestrationContext){
            bootstrapCmdline = new String[]{BOOTSTRAP_PATH, "slipstream-orchestrator"};
            nodename = getOrchestratorName(run);
        } else {
            bootstrapCmdline = new String[]{BOOTSTRAP_PATH};
            nodename = Run.MACHINE_NAME;
        }

        final Script script = new Script(SLIPSTREAM_REPORT_DIR, LOG_FILENAME);
        final Script defineExports = script.similar();
        final Script doOrchestratorStaff = script.similar();
        final Script doNonOrchestratorStaff = script.similar();
        final Script runBootstrap = script.similar();

        defineExports.
            export("SLIPSTREAM_CLOUD", getCloudServiceName()).
            export("SLIPSTREAM_CONNECTOR_INSTANCE", getConnectorInstanceName()).
            export("SLIPSTREAM_NODENAME", nodename).
            export("SLIPSTREAM_DIID", run.getName()).
            export("SLIPSTREAM_REPORT_DIR", SLIPSTREAM_REPORT_DIR).
            export("SLIPSTREAM_SERVICEURL", configuration.baseUrl).
            export("SLIPSTREAM_BUNDLE_URL", configuration.getRequiredProperty("slipstream.update.clienturl")).
            export("SLIPSTREAM_BOOTSTRAP_BIN", configuration.getRequiredProperty("slipstream.update.clientbootstrapurl")).
            export("SLIPSTREAM_CATEGORY", run.getCategory().toString()).
            export("SLIPSTREAM_USERNAME",           username).
            export("SLIPSTREAM_COOKIE",             getCookieForEnvironmentVariable(username, run.getUuid())).
            export("SLIPSTREAM_VERBOSITY_LEVEL",    getVerboseParameterValue(user)).
            nl().
            export("CLOUDCONNECTOR_BUNDLE_URL", configuration.getRequiredProperty(constructKey(UserParametersFactoryBase.UPDATE_CLIENTURL_PARAMETER_NAME))).
            export("CLOUDCONNECTOR_PYTHON_MODULENAME", CLOUDCONNECTOR_PYTHON_MODULENAME).
            export("OKEANOS_SERVICE_TYPE", configuration.getRequiredProperty(constructKey(OkeanosUserParametersFactory.SERVICE_TYPE_PARAMETER_NAME))).
            export("OKEANOS_SERVICE_NAME", configuration.getRequiredProperty(constructKey(OkeanosUserParametersFactory.SERVICE_NAME_PARAMETER_NAME))).
            export("OKEANOS_SERVICE_REGION", configuration.getRequiredProperty(constructKey(OkeanosUserParametersFactory.SERVICE_REGION_PARAMETER_NAME)))
        ;

        // Orchestrator is very stripped down now that we rely on CELAR-certified images.
        // All needed functionality is builtin in the image.
        doOrchestratorStaff.
            nl().
            comment("Generate keypair").
            command("ssh-keygen", "-t", "rsa", "-N", "", "-f", "~/.ssh/id_rsa", "<", "/dev/null", "||", "true").
            nl().
            comment("Run an orchestrator-specific script").
            // For a VM instance that plays the role of an orchestrator
            commandL("[ -x /root/okeanos-orch-custom.sh ] && /root/okeanos-orch-custom.sh")
        ;

        doNonOrchestratorStaff.
            nl().
            comment("Run a node-specific script (for a node that is not started by an orchestrator)").
            // Unfortunately (?), there is one more case to handle but it cannot be done here:
            // A node that *is* started by an orchestrator. This is handled by python code
            // so we must patch the respective python code (OkeanosClientCloud._get_init_script).
            commandL("[ -x /root/okeanos-node-custom.sh ] && /root/okeanos-node-custom.sh")
        ;

        runBootstrap.
            logBegin("Downloading", "$SLIPSTREAM_BOOTSTRAP_BIN", "to", BOOTSTRAP_PATH).
            commandL(
                "wget", "--secure-protocol=SSLv3", "--no-check-certificate", "-O",
                BOOTSTRAP_PATH,
                "$SLIPSTREAM_BOOTSTRAP_BIN").
            command("chmod", "0755", BOOTSTRAP_PATH).
            logEnd("Downloading", "$SLIPSTREAM_BOOTSTRAP_BIN", "to", BOOTSTRAP_PATH).
            nl().
            commandL(bootstrapCmdline)
        ;

        // Finally, the actual, assembled contextualization script
        script.
            hashbang("/bin/bash").
            comment("+ Slipstream contextualization script for ~Okeanos").
            nl().
            command("mkdir -p /tmp/slipstream/reports").
            nl().
            logBegin().
                include(defineExports).
                nl().
                includeIf(inOrchestrationContext, doOrchestratorStaff, doNonOrchestratorStaff).
                include(runBootstrap).
                nl().
            logEnd().
            nl().
            comment("- Slipstream contextualization script for ~Okeanos")
        ;

        return script.toString();
    }

    private List<String> getRunInstanceCmdline(Run run, User user) throws SlipStreamClientException, IOException, ConfigurationException, ServerExecutionEnginePluginException, AbortException {
        // The value provided by the standard SlipStream implementation.
        final String standardPublicSshKey = getPublicSshKey(run, user).trim();

        // For ~Okeanos we augment this with the user-provided SSH key.
        final String extraPublicSshKey = user.getParameter(
            ExecutionControlUserParametersFactory.CATEGORY + "." + UserParametersFactoryBase.SSHKEY_PARAMETER_NAME
        ).getValue().trim();

        final String publicSshKey;
        if(standardPublicSshKey.equals(extraPublicSshKey)) {
            publicSshKey = standardPublicSshKey;
        }
        else {
            publicSshKey = format("%s\n%s", standardPublicSshKey, extraPublicSshKey);
        }

        try {
            final List<String> commonParams = getCommonParams(user);
            final String vdiskSizeName = "--volatile-disk-size"; // Use the same string in OkeanosCommand.py
            String vdiskSize = getVolatileDiskSize(run);
            if(vdiskSize == null) {
                vdiskSize = "0";
            }

            commonParams.add(vdiskSizeName);
            commonParams.add(vdiskSize);

            return mkList(
                COMMAND_RUN_INSTANCES,
                commonParams,
                "--instance-type", getInstanceType(run),
                "--image-id", getImageId(run, user),
                "--instance-name", getVmName(run),
                "--network-type", getNetwork(run),
                "--security-groups", getSecurityGroups(run),
                "--public-key", publicSshKey,
                "--context-script", createContextualizationData(run, user)
            );
        }
        catch(Exception e) {
            StringWriter sw = new StringWriter();
            PrintWriter pw = new PrintWriter(sw);
            e.printStackTrace(pw);
            log.info("!!ERROR " + e + "\n" + sw.toString());
            throw e;
        }
    }

    private String trimTo(StringBuilder s, int length) {
        if(s.length() <= length) {
            return s.toString();
        } else if(length <= 3) {
            return s.substring(0, length);
        }
        else {
            return s.substring(0, length - 3) + "...";
        }
    }

    private String exec(
        List<String> cmdline,
        boolean printStdout, boolean printStderr,
        boolean printAccStdout, boolean printAccStderr
    ) throws IOException, InterruptedException {
        final class OutputThread extends Thread {
            final String logPrefix;
            final InputStream in;
            final StringBuilder sb;
            final boolean printLines;

            OutputThread(boolean printLines, String logPrefix, InputStream in, StringBuilder sb) {
                this.printLines = printLines;
                this.logPrefix = logPrefix;
                this.in = in;
                this.sb = sb;
            }

            @Override
            public void run() {
                final InputStreamReader isr = new InputStreamReader(in);
                final BufferedReader br = new BufferedReader(isr);

                String line = null;
                try {
                    while((line = br.readLine()) != null) {
                        if(printLines) { log.info(logPrefix + line); }
                        sb.append(line);
                        sb.append(System.getProperty("line.separator"));
                    }
                    if(sb.length() > 0) {
                        sb.setLength(sb.length() - 1);
                    }

                    in.close();
                }
                catch(IOException e) {
                    e.printStackTrace();
                }
            }
        }

        final StringBuilder cmdsb = new StringBuilder();
        for(String s : cmdline) {
            cmdsb.append(s);
            cmdsb.append(' '); // never mind one more
        }
        final String trimmedCmd = trimTo(cmdsb, 80);

        log.info(cmdsb.toString());

        final StringBuilder stdoutBuffer  = new StringBuilder(1024);
        final StringBuilder stderrBuffer = new StringBuilder(1024);
        final ProcessBuilder pb = new ProcessBuilder(cmdline);
        final Process proc = pb.start();
        final OutputThread stdoutThread = new OutputThread(printStdout, "STDOUT ", proc.getInputStream(), stdoutBuffer);
        final OutputThread stderrThread = new OutputThread(printStderr, "STDERR ", proc.getErrorStream(), stderrBuffer);

        stdoutThread.start();
        stderrThread.start();
        final int procResult = proc.waitFor();
        stdoutThread.join();
        stderrThread.join();

        if(stdoutBuffer.length() > 0 && printAccStdout) { log.info("STDOUT of " + trimmedCmd + "\n" + stdoutBuffer); }
        if(stderrBuffer.length() > 0 && printAccStderr) { log.info("STDERR of " + trimmedCmd + "\n" + stderrBuffer); }

        if(procResult != 0) {
            final String msg = "Exit code " + procResult + " from " + trimmedCmd;
            System.err.println(msg);
            if(stdoutBuffer.length() > 0 && !printAccStdout) { log.info("STDOUT of " + trimmedCmd + "\n" + stdoutBuffer); }
            if(stderrBuffer.length() > 0 && !printAccStderr) { log.info("STDERR of " + trimmedCmd + "\n" + stderrBuffer); }
            throw new ProcessException(msg, stdoutBuffer.toString());
        }

        return stdoutBuffer.toString();
    }

    public static final class RunInstanceReturnData {
        public final String instanceId;
        public final String ipv4;
        public final int exitCode;
        public final String adminPass;

        public RunInstanceReturnData(String instanceId, String ipv4, int exitCode, String adminPass) {
            this.instanceId = instanceId;
            this.ipv4 = ipv4;
            this.exitCode = exitCode;
            this.adminPass = adminPass;
        }

        @Override
        public boolean equals(Object o) {
            if(this == o) {
                return true;
            }
            if(o == null || getClass() != o.getClass()) {
                return false;
            }

            RunInstanceReturnData that = (RunInstanceReturnData) o;

            return exitCode == that.exitCode && adminPass.equals(that.adminPass) && instanceId.equals(that.instanceId) && ipv4.equals(that.ipv4);

        }

        @Override
        public int hashCode() {
            int result = instanceId.hashCode();
            result = 31 * result + ipv4.hashCode();
            result = 31 * result + exitCode;
            result = 31 * result + adminPass.hashCode();
            return result;
        }

        @Override
        public String toString() {
            final StringBuilder sb = new StringBuilder("RunInstanceReturnData(");
            sb.append("instanceId='").append(instanceId).append('\'');
            sb.append(", ipv4='").append(ipv4).append('\'');
            sb.append(", exitCode=").append(exitCode);
            sb.append(", adminPass='").append(adminPass).append('\'');
            sb.append(')');
            return sb.toString();
        }
    }

    protected void checkScannerNext(
        Scanner scanner,
        String stdout,
        String whatToParse
    ) throws SlipStreamClientException {
        if(!scanner.hasNext()) {
            throw new SlipStreamClientException("Error returned by launch command. Could not parse " + whatToParse + " from '" + stdout + "'");
        }
    }
    protected RunInstanceReturnData _parseRunInstanceResult(String stdout) throws SlipStreamClientException {
        final Scanner scanner = new Scanner(stdout);

        checkScannerNext(scanner, stdout, "instanceId [at index 0]");
        final String instanceId = scanner.next();

        checkScannerNext(scanner, stdout, "ipv4  [at index 1]");
        final String ipv4 = scanner.next();

        checkScannerNext(scanner, stdout, "exitCode  [at index 2]");
        final int exitCode = scanner.nextInt();

        checkScannerNext(scanner, stdout, "adminPass  [at index 3]");
        final String adminPass = scanner.next();

        return new RunInstanceReturnData(instanceId, ipv4, exitCode, adminPass);
    }

    public Run launch(Run run, User user) throws SlipStreamException {
        final String methodInfo = format("launch(%s)", user);
        log.entering(ClassName, methodInfo);
        try {
            validateRun(run, user);
            final List<String> cmdline = getRunInstanceCmdline(run, user);
            final String result = exec(cmdline, true, true, false, false);

            final RunInstanceReturnData instanceData = _parseRunInstanceResult(result);
            log.info(instanceData.toString());

            updateInstanceIdAndIpOnRun(run, instanceData.instanceId, instanceData.ipv4);
        } catch (IOException|InterruptedException e) {
            log.log(Level.SEVERE, "launch", e);
            throw new SlipStreamException("Failed getting run instance command", e);
        } catch (ProcessException e) {
            log.log(Level.SEVERE, "launch", e);
            try {
                final String stdOut = e.getStdOut();
                log.log(Level.SEVERE, "stdout (from script) =" + stdOut);
                final String[] instanceData = parseRunInstanceResult(stdOut);
                updateInstanceIdAndIpOnRun(run, instanceData[0], instanceData[1]);
            } catch (Exception ex) {
                log.log(Level.WARNING, "launch: updateInstanceIdAndIpOnRun()", ex);
            }
            throw e;
        }
        finally {
            log.exiting(ClassName, methodInfo);
            deleteTempSshKeyFile();
        }

        return run;
    }

    public Credentials getCredentials(User user) {
        return new OkeanosCredentials(user, getConnectorInstanceName());
    }

    protected Properties _parseDescribeInstanceResult(String stdout) throws SlipStreamException {
        final Properties props = new Properties();
        final StringReader sr = new StringReader(stdout);
        final BufferedReader br = new BufferedReader(sr);
        String line;
        try {
            while((line = br.readLine()) != null) {
                final Scanner scanner = new Scanner(line);
                if(!scanner.hasNext()) {
                    throw new SlipStreamException("Error returned by launch command. Got: " + line);
                }
                final String instanceId = scanner.next();
                if(!scanner.hasNext()) {
                    throw new SlipStreamException("Error returned by launch command. Got: " + line);
                }
                final String status = scanner.next();

                props.put(instanceId, status);
            }
        }
        catch(IOException e) {
            throw new SlipStreamException("While parsing describe instance results", e);
        }

        return props;
    }

    public Properties describeInstances(User user) throws SlipStreamException {
        final String methodInfo = format("describeInstances(%s)", user);
        log.entering(ClassName, methodInfo);
        validateCredentials(user);

        final List<String> cmdline = mkList(COMMAND_DESCRIBE_INSTANCES, getCommonParams(user));
        try {
            final String result = exec(cmdline, false, false, true, true);
            return _parseDescribeInstanceResult(result);
        } catch (IOException|InterruptedException e) {
            log.log(Level.SEVERE, "describeInstances", e);
            throw new SlipStreamInternalException(e);
        } catch (ProcessException e) {
            log.log(Level.SEVERE, "describeInstances", e);
            throw e;
        }
        finally {
            log.exiting(ClassName, methodInfo);
        }
    }

    public void terminate(Run run, User user) throws SlipStreamException {
        final String methodInfo = format("terminate(%s, %s)", run, user);
        log.entering(ClassName, methodInfo);
        validateCredentials(user);

        final List<String> cmdlineTpl = mkList(
            COMMAND_TERMINATE_INSTANCES,
            getCommonParams(user),
            "--instance-id"
        );

        for (final String id : getCloudNodeInstanceIds(run)) {
            final List<String> cmdline = mkList(cmdlineTpl, id);

            try {
                log.info("Terminating " + id);
                exec(cmdline, false, false, true, true);
                log.info("Terminated " + id);
            } catch (IOException|InterruptedException e) {
                log.log(Level.WARNING, "terminate()", e);
            } catch (ProcessException e) {
                log.log(Level.SEVERE, "terminate()", e);
                throw e;
            }
        }

        log.exiting(ClassName, methodInfo);
    }

    @Override
    public Map<String, UserParameter> getUserParametersTemplate() throws ValidationException {
        return new OkeanosUserParametersFactory(getConnectorInstanceName()).getParameters();
    }
}
