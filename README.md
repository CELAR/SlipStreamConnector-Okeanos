# SlipStreamConnector-Okeanos

Source code for SlipStream ~Okeanos connector.

## Status

The connector is in version `0.5.0-SNAPSHOT`, based on SlipStrtream version `2.3.4-SNAPSHOT`. We use Java 1.7.

| Capability            | Status |
|-----------------------| :----: |
| Run Image             |   ✓   |
| Run Deployment        |   ✓   |   
| Build Image           |   [#4](https://github.com/CELAR/SlipStreamConnector-Okeanos/issues/4)   |
| Volatile disk         |   ✓   |


## Installation

### Slipstream Server
In the Slipstream Server installation script, you must set

```
RELEASE=false
```

so that the snapshot repositories are picked up. The current version of the connector is `0.5.0-SNAPSHOT`, as given in
the [pom.xml](pom.xml). After the SlipStream Server installation, just run

```
$ yum install slipstream-connector-okeanos
$ yum install slipstream-connector-okeanos-python
```

and then restart the SlipStream Server via

```
$ service slipstream restart
```

for the java code (the Java part of the connector) to take effect.

### IaaS support libraries
In order for the ~Okeanos connector to be fully functional, you need to install the ~Okeanos python support library, named `kamaki`, in the machine that hosts the SlipStream Server.

	$ pip install kamaki


## Certified images [2014-09-18]
As of 2014-09-18, a VM image that is to be used as an Orchestrator must have preinstalled software in it. We call these images *CELAR-certified*. The rationale is to move ad-hoc and distribution-sensitive code out of the connector, in order to minimize complexity. For the time being, we provide a recipe for an Ubuntu-based such image [here](vmrecipes/celar-ubuntu-14.04-LTS.md).

An Ubuntu public image with the above characteristics is already published in ~Okeanos production:

```
$ kamaki image info fe31fced-a3cf-49c6-b43b-f58f5235ba45
name: CELAR-Ubuntu-14.04-LTS
checksum: e3069718eaf4990fbc2805ce3d42dffa4bee5aed7f5ee664486a7f1dc455e217
updated-at: 2014-09-18 12:10:58
created-at: 2014-09-18 12:10:58
id: fe31fced-a3cf-49c6-b43b-f58f5235ba45
deleted-at: 
location: pithos://fc95f201-d5a9-46fa-8ede-b8983b420a40/images/CELAR-Ubuntu-14.04-LTS
is-public: True
owner: fc95f201-d5a9-46fa-8ede-b8983b420a40 (loverdos@gmail.com)
disk-format: diskdump
size: 2.15GiB
properties:
    PARTITION_TABLE: msdos
    OSFAMILY: linux
    DESCRIPTION: Ubuntu 14.04.1 LTS
    OS: ubuntu
    ROOT_PARTITION: 1
    USERS: user
container-format: bare
```


## Breaking change [2014-10-15]
The upcoming version `0.16` of [Synnefo](https://www.synnefo.org), the IaaS software that ~Okeanos is based on and which is needed to support the Add Extra Volatile Disk feature, introduces a breaking change in the `kamaki` software. This is reported and explained in the respective ticket [The new SSL authentication handling breaks software using kamaki](https://github.com/grnet/kamaki/issues/72), opened 2014-10-15. 

The breaking change is always present if `kamaki` is installed via `pip` and you will see the following or similar behavior in the command line:

```
$ kamaki image list
Unknown Error: [Errno 185090050] _ssl.c:330: error:0B084002:x509 certificate routines:X509_load_cert_crl_file:system lib
```

Please refer to the above ticket and its comments for an explanation and further pointers to documentation.

### Workaround/Solution
By installing `kamaki` via `pip` the procedure in only manual and you need to set a path for the certificates. The command

```
$ kamaki config get ca_certs
```

will normally output

```
ca_certs not found
```

since no path has been automatically set by the installation procedure of `kamaki`.

In order to overcome this in my Mac dev box + Homebrew, I install `openssl`:

```
$ brew install openssl
```

which places the certificates in `/usr/local/etc/openssl/cert.pem` and then:

```
$ kamaki config set ca_certs /usr/local/etc/openssl/cert.pem
```


A similar procedure applies to other environments. After that we are back to normal:

```
$ kamaki config get ca_certs
/usr/local/etc/openssl/cert.pem

$ kamaki image list
fe31fced-a3cf-49c6-b43b-f58f5235ba45 CELAR-Ubuntu-14.04-LTS
    status: available
    container_format: bare
    disk_format: diskdump
    size: 2.15GiB
    
...
```

Please see [celar-ubuntu-14.04-LTS](vmrecipes/celar-ubuntu-14.04-LTS.md) for the correct procedure regarding our CELAR-certified Ubuntu VM image.

## License
This software is under [Apache v2](LICENSE.txt)
