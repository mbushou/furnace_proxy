Furnace Message Proxy
=======

<img align="right" width=20% src="https://github.com/mbushou/furnace/blob/master/misc/logo_smoke_sm.png">

Introduction
-------
The Furnace message proxy relays IPC messages from a tenant's app (inside the
cloud) to the matching tenant backend (outside the cloud).

A single message proxy instance relays traffic between a single app and its
backend.  For example, a tenant use case that calls for six app instances
connecting to a single backend would require six message proxy instances.

Please see ./docs for the pydoc documentation.

For more information on the Furnace project, visit its [main repository](https://github.com/mbushou/furnace).

Installation
-------
See [INSTALL.md](https://github.ncsu.edu/mbushou/furnace/blob/master/INSTALL.md) for instructions on installing Furnace in a single-hypervisor configuration.

Running the proxy
-------

The proxy requires six arguments:

1. `--ak` path to app's key
1. `--bk` path to backend's key
1. `--ip` interior IP that the proxy should bind to
1. `--it` interior port that the proxy should bind to
1. `--ep` the tenant's external IP hosting the backend (must be
   internet-routable)
1. `--et` the tenant's external port hosting the backend

Example:

```
python3 $PROXY_DIR/proxy.py -d \
        --ak $FURNACE_DIR/tenant_data/124-124-124-app/app.key_secret \
        --bk $FURNACE_DIR/tenant_data/124-124-124-app/be.key_secret \
        --ip 127.0.0.1 \
        --it 5561 \
        --ep 127.0.0.1 \
        --et 5563"
```

During normal operation, the message proxy prints a period '.' once per second.  Exit the message proxy using ctrl-C.

License
-------
Furnace is GPLv3.

However, to use Furnace library with DRAKVUF, you must also comply with DRAKVUF's license.
Including DRAKVUF within commercial applications or appliances generally
requires the purchase of a commercial DRAKVUF license (see
https://github.com/tklengyel/drakvuf/blob/master/LICENSE).
