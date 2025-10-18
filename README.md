# shma Redis service role

## Network policy

The default `NetworkPolicy` denies traffic unless the caller is labeled with `shma.dev/redis-access: "true"`. Set the label on every workload that needs Redis access or override `redis_network_policy_allowed_peers` to add explicit peers. The policy advertises `shma.dev/rate-limiting` guidance describing the expected namespace-level rate limiting implementation; the string can be overridden through `redis_rate_limit_documentation`.

## Transport security

TLS can be enabled by setting `redis_tls_enabled: true`. When enabled the role exposes `redis_tls_port` (default `6380`), mounts certificates from `redis_tls_cert_secret_name`, and updates health checks, liveness probes, and optional exporters. Plaintext can be disabled via `redis_enable_plaintext_port: false`. Provide a secret with `tls.crt`, `tls.key`, and `ca.crt` (keys configurable via the `redis_tls_cert_secret_*` variables) and ensure clients trust the CA.

## Authentication and ACLs

ACLs are enabled by default. The role builds an ACL file from `redis_acl_users` and, when a `redis_password` is provided, automatically creates a limited application user derived from that password. Set `redis_manage_acl_secret: true` to have the role publish the ACL secret, or provide your own secret if you need to manage credentials externally. Every ACL definition must include at least one enabled user—if no enabled entries are found the role fails early. Customize `redis_acl_users` or supply a fully managed ACL through `redis_acl_content`.

ACL syntax is validated before the manifests are applied. By default the controller host must provide `redis-server` and `redis-cli`; the role spins up a temporary local instance and runs `ACL LOAD` to verify syntax. If you prefer a custom validation tool, define `redis_acl_validator_command` and include the `%ACL_FILE%` placeholder where the temporary ACL file path should be substituted. Set `redis_acl_validate: false` to skip validation entirely (not recommended).

After resources are applied the role automatically issues `ACL LOAD` inside the first Redis pod so runtime changes become active without restarting the StatefulSet.

## Runtime exports

Service exports now include TLS metadata:

```yaml
redis_service_exports:
  env:
    REDIS_HOST: redis
    REDIS_PORT: "6379"
    REDIS_TLS_PORT: "6380"
    REDIS_TLS_ENABLED: "false"
```

Override the block if you need custom keys for your downstream configuration systems.

## Persistence and durability

Append-only files are stored on disk-backed `emptyDir` volumes by default. Set `redis_appendonlydir_enabled` to `false` to skip the mount or provide custom sizing via `redis_appendonlydir_size_limit`. If you switch the `emptyDir` medium to `Memory` the role automatically relaxes `appendfsync` to `no` to avoid unnecessary write amplification on tmpfs.

RDB snapshots are configured through `redis_save_points`, which defaults to the stock Redis recommendations. Adjust the list (or set it to an empty list) to change snapshot cadence.

An optional backup CronJob can be enabled with `redis_backup_enabled: true`. The job defaults to using `redis-cli --rdb` to emit an RDB file into `/backup`. Provide object storage credentials via `redis_backup_extra_env`, tune the cadence with `redis_backup_schedule`, and override `redis_backup_command` if you need to push the artifact to S3, GCS, or another target.

## Monitoring and observability

Enable Prometheus metrics with `redis_enable_metrics: true`. The role injects `redis_exporter` as a sidecar, wiring TLS and password secrets automatically. Slow-log sampling is enabled through `redis_slowlog_log_slower_than` and `redis_slowlog_max_len` to aid debugging.

## Resource management

Sensible defaults are applied for `redis_resources` (`256Mi` request/`512Mi` limit) and `redis_maxmemory` (`2gb`) so pods do not consume unbounded node resources. Customize these values to match your workload profile. Connection-level protection is enforced via `redis_maxclients` (default `10000`); pair this with namespace rate limiting as described earlier for brute-force resistance.

## LXC runtime notes

The LXC adapter mirrors the Kubernetes security posture: ACLs are written to `/etc/redis/users.acl` when enabled, tmpfs mounts are verified before Redis starts, and the cloud-init script fails fast if Redis does not start cleanly. Health checks remain published under the `checks` block—integrate these with your chosen orchestration or monitoring system.
