---
title: "Service Restart Loop Response"
slug: service-restart-loop
id: RB-008
tags: systemd, restart, loop, crashloop, process, supervisor, kubernetes
severity: critical
illustrative: true
---

> **ILLUSTRATIVE RUNBOOK** — This runbook is provided as a reference template.
> Adapt service names, paths, and commands to your specific environment before use.

# Service Restart Loop Response

## Symptoms
- Systemd reports `start request repeated too quickly` and enters `failed` state
- Service restarts > 3 times within 5 minutes
- Kubernetes pod shows `CrashLoopBackOff` with increasing `RESTARTS` count
- CPU and disk I/O spikes at regular intervals corresponding to restart cadence
- Application logs contain rapid repeated startup sequences followed by abrupt termination
- Monitoring alert: `service_restarts_total > threshold` over short window

## Possible Causes
1. **Configuration error** — invalid config file or missing required environment variable
2. **Missing dependency** — required service, socket, or database not ready at startup
3. **Port conflict** — another process already occupying the required port
4. **Insufficient permissions** — cannot read config file, write PID file, or bind to port < 1024
5. **Resource exhaustion at startup** — OOM kill immediately after startup (see `oom-kill` runbook)
6. **Corrupt binary or bad deployment** — application binary fails immediately after update
7. **Dependency service also crashing** — cascading failure from an upstream dependency
8. **Startup probe failing in Kubernetes** — readiness/liveness probe timeout too short

## Investigation Steps

1. **Determine how many restarts have occurred:**
   ```bash
   systemctl show <service-name> --property=NRestarts,ActiveState,SubState,Result
   journalctl -u <service-name> --since "30 minutes ago" | grep -E "Starting|Started|Failed|Stopped"
   ```

2. **Read the last exit reason:**
   ```bash
   journalctl -u <service-name> -n 50 --no-pager
   # Look for: ExecStart failed, exit code, signal name
   ```

3. **Check for port conflicts:**
   ```bash
   ss -tlnp | grep <port>
   lsof -i :<port>
   ```

4. **Verify required environment variables and config files:**
   ```bash
   systemctl cat <service-name>          # view unit environment settings
   # Check the EnvironmentFile or Environment lines
   # Verify the config file is readable
   test -r /etc/<service>/config.yml && echo "readable" || echo "MISSING or UNREADABLE"
   ```

5. **Check dependency services are running:**
   ```bash
   systemctl list-dependencies <service-name>
   # Verify each listed dependency is active
   systemctl is-active <dependency-service>
   ```

6. **Look for OOM kill at startup:**
   ```bash
   dmesg | grep -i "oom\|killed" | tail -20
   journalctl -k | grep -i "out of memory\|oom-kill" | tail -10
   ```

7. **Check file permissions:**
   ```bash
   ls -la /etc/<service>/config.yml
   ls -la /var/run/<service>.pid 2>/dev/null
   ls -la /var/log/<service>/ 2>/dev/null
   # Compare with the User= and Group= in the unit file
   ```

8. **For Kubernetes: inspect pod events and logs:**
   ```bash
   kubectl describe pod <pod-name> -n <namespace>
   kubectl logs <pod-name> -n <namespace> --previous  # last crashed container
   kubectl get events -n <namespace> --sort-by='.lastTimestamp' | tail -20
   ```

9. **Test manual startup to capture output directly:**
   ```bash
   # Run as the service user to replicate permissions
   sudo -u <service-user> /usr/bin/<service-binary> --config /etc/<service>/config.yml
   # Observe the exact error before it exits
   ```

## Remediation

### Stop the restart loop first (operator-approved):
```bash
# Prevent further automatic restarts while you investigate
systemctl stop <service-name>
# For Kubernetes: scale to 0 replicas
kubectl scale deployment/<deployment-name> --replicas=0 -n <namespace>
```

### Fix configuration errors:
```bash
# Validate config syntax (tool depends on the service)
<service-binary> --config-check /etc/<service>/config.yml
# Fix the error, then verify:
systemctl start <service-name>
systemctl status <service-name>
```

### Resolve port conflicts:
```bash
# Identify and stop the conflicting process (verify before killing)
lsof -i :<port> -t | xargs -r kill -15
# Or change the service port in its configuration
```

### Fix missing environment variable:
```bash
# Add to the systemd override
systemctl edit <service-name>
# Add under [Service]:
# Environment="MISSING_VAR=value"
systemctl daemon-reload && systemctl start <service-name>
```

### Roll back a bad deployment:
```bash
# Revert to the previous binary or container image
# Kubernetes:
kubectl rollout undo deployment/<deployment-name> -n <namespace>
kubectl rollout status deployment/<deployment-name> -n <namespace>
# Systemd / package manager:
apt-get install <package>=<previous-version>
```

### Fix permissions:
```bash
chown -R <service-user>:<service-group> /var/log/<service>/ /etc/<service>/
chmod 640 /etc/<service>/config.yml
```

## Verification Steps
1. Service is running and stable for 5+ minutes: `watch systemctl status <service-name>`
2. Restart count is not incrementing: `systemctl show <service-name> --property=NRestarts`
3. Health endpoint responds correctly: `curl -s http://localhost:<port>/health`
4. No new error entries in journal: `journalctl -u <service-name> --since "now" -f`

## Escalation
- If the loop persists after fixes: escalate to the service owner and infrastructure team
- If a bad deployment caused the loop: initiate a rollback P1 process
- If a Kubernetes node is suspected: cordon the node and reschedule pods

## Prevention
- Configure `StartLimitIntervalSec` and `StartLimitBurst` in systemd to limit restart rate
- Use `ExecStartPre=` to validate config before the main process starts
- Implement a readiness check: only restart when the service is actually unhealthy
- In Kubernetes: set `initialDelaySeconds` appropriately for startup probes
- Alert on `NRestarts > 3` within 10 minutes; page on-call before systemd gives up
