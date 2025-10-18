# shma Redis service role

## Network access labels

The default `NetworkPolicy` only admits pods that declare the label `shma.dev/redis-access: "true"`. Consumers deploying into Kubernetes should add this label to any workload that requires Redis connectivity. The label key/value can be overridden by editing `redis_network_policy_allowed_peers` in role variables, but the default contract expects peers to opt in through that label.

## Runtime exports

The role publishes a service export block with `REDIS_HOST` and `REDIS_PORT` so dependent applications can discover connection details without hardcoding them. The defaults resolve to the Kubernetes service name/port or the runtime adapter's advertised address when using other backends. Override `redis_service_exports` if you need different values.

## Ephemeral append-only storage

Redis append-only files are placed on a tmpfs mount by default through the `redis_ephemeral_mounts.appendonlydir` settings. Kubernetes runtimes attach an `emptyDir` volume with `medium: Memory`, and the LXC adapter provisions a tmpfs mount and `/etc/fstab` entry. Adjust `redis_appendonlydir_*` variables if the default size or options do not suit your deployment.
