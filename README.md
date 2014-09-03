# SlipStreamConnector-Okeanos

Source code for SlipStream ~Okeanos connector.

## Status

| Capability            | Status |
|-----------------------| :----: |
| Run Image             |   ✓   |
| Run Deployment        |   ✓   |   
| Build Image           |   ✗   |
| Extra disk volatile   |   ✗   |
| Extra disk persistent |   ✗   |

## Installation
### Slipstream Server
In order for the ~Okeanos connector to be fully functional, you need to install the ~Okeanos python support library, named `kamaki`, in the machine that hosts the SlipStream Server.

	$ pip install kamaki