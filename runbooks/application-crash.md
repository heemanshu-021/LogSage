---
title: "Application Process Crash Response"
slug: application-crash
id: RB-006
tags: process, crash, coredump, signal, application, sigkill, sigsegv
severity: critical
illustrative: true
---

> **ILLUSTRATIVE RUNBOOK** — This runbook is provided as a reference template.
> Adapt paths, service names, and commands to your specific environment before use.

# Application Process Crash Response

## Symptoms
- Service process exits unexpectedly with non-zero exit code
- `Segmentation fault (core dumped)` or `Killed` in process output
- Systemd reports `Main process exited, code=killed, status=11/SEGV` or `status=9/KILL`
- Application log file ends abruptly without shutdown message
- Monitoring alert: process PID missing, health check returning `Connection refused`

## Possible Causes
1. **Segmentation fault** — invalid memory access, null pointer dereference, stack overflow
2. **OOM kill** — kernel killed the process due to memory pressure (see `oom-kill` runbook)
3. **Unhandled exception** — uncaught exception or panic reaching top-level handler
4. **Signal from external process** — `SIGKILL` sent by deployment tooling or operator
5. **Corrupt binary or library** — shared library version mismatch after a partial upgrade
6. **Resource limit exceeded** — `RLIMIT_NOFILE`, `RLIMIT_NPROC`, or cgroup limits

## Investigation Steps

1. **Check if the process is running:**
   ```bash
   systemctl status <service-name>
   pgrep -a <process-name>
   ```

2. **Read the last exit status and reason:**
   ```bash
   systemctl show <service-name> --property=ExecMainStatus,Result
   journalctl -u <service-name> --since "10 minutes ago" --no-pager | tail -100
   ```

3. **Look for OOM kill in kernel log:**
   ```bash
   journalctl -k | grep -i "oom\|killed process" | tail -20
   dmesg | grep -i "oom\|segfault\|killed" | tail -20
   ```

4. **Check for core dump:**
   ```bash
   ls -lh /var/crash/ /tmp/core* /core 2>/dev/null
   coredumpctl list --since "1 hour ago"
   coredumpctl info <PID>
   ```

5. **Inspect the application log for the final error:**
   ```bash
   tail -200 /var/log/<service-name>/app.log
   # or if using journald:
   journalctl -u <service-name> -n 200 --no-pager
   ```

6. **Check resource limits at time of crash:**
   ```bash
   # Open file descriptors for running process
   cat /proc/<PID>/limits 2>/dev/null
   ulimit -a
   # cgroup memory limit
   cat /sys/fs/cgroup/memory/<service>/memory.limit_in_bytes 2>/dev/null
   ```

7. **Inspect library dependencies:**
   ```bash
   ldd /usr/bin/<service-binary> | grep "not found"
   ```

## Remediation

### Immediate: Restart the service (operator-approved)
```bash
# Review the logs above BEFORE restarting to avoid masking root cause
systemctl restart <service-name>
systemctl status <service-name>
```

### If a core dump is available: analyse with gdb (developer action)
```bash
# Do not delete the core dump before analysis
coredumpctl gdb <PID>
(gdb) bt         # print backtrace
(gdb) info registers
```

### If library mismatch caused the crash:
```bash
# Identify which package owns the library
dpkg -S /usr/lib/<library>.so   # Debian/Ubuntu
rpm -qf /usr/lib/<library>.so   # RHEL/CentOS
# Reinstall the owning package
apt-get install --reinstall <package>
```

### If resource limits are the cause:
```bash
# Increase open-file limit for the service (systemd)
# Edit /etc/systemd/system/<service>.service.d/override.conf:
# [Service]
# LimitNOFILE=65536
systemctl daemon-reload && systemctl restart <service-name>
```

## Verification Steps
1. Confirm process is running: `systemctl is-active <service-name>`
2. Health-check endpoint responds: `curl -s http://localhost:<port>/health | jq .`
3. No new crash entries in journal: `journalctl -u <service-name> --since "now" -f`
4. Monitor for 5 minutes before closing the incident

## Escalation
- If the process crashes again within 15 minutes: escalate to on-call engineering lead
- If a core dump shows a third-party library crash: open a vendor ticket and preserve the dump
- If OOM is the root cause: follow the `oom-kill` runbook

## Prevention
- Configure `Restart=on-failure` and `RestartSec=10s` in the systemd unit
- Set up crash alerting via PID monitoring in your observability stack
- Enable core dumps in a controlled location: `kernel.core_pattern=/var/crash/core.%e.%p`
- Review memory and file-descriptor limits before each deployment
