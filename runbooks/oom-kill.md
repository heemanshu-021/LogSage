---
title: "Out of Memory (OOM) Kill Response"
slug: oom-kill
id: RB-002
tags: kernel, oom, memory, linux, process
severity: critical
illustrative: true
---

> **ILLUSTRATIVE RUNBOOK** — This runbook is provided as a reference template.
> Adapt service names and thresholds to your specific environment before use.

# Out of Memory Kill Response

## Symptoms
- `kernel: Out of memory: Kill process` in syslog
- `oom-kill:constraint=CONSTRAINT_NONE` kernel messages
- Service unexpectedly exits / restarts

## Possible Causes
1. **Application memory leak or unbound cache growth**
2. **Spike in concurrent requests exceeding allocated RAM**
3. **Misconfigured cgroup or container memory limits (lower than footprint)**
4. **Heavy background batch jobs running on production worker nodes**
5. **JVM heap configured higher than available container memory**

## Investigation Steps

1. **Identify what was killed and when:**
   ```bash
   grep -i "oom\|killed process" /var/log/syslog | tail -50
   journalctl -k | grep -i oom | tail -20
   ```

2. **Current memory pressure:**
   ```bash
   free -h
   vmstat -s | grep -i mem
   cat /proc/meminfo | head -20
   ```

3. **Top memory consumers:**
   ```bash
   ps aux --sort=-%mem | head -20
   ```

## Remediation

### Immediate
```bash
# Restart the killed service
systemctl restart <service-name>

# If swap is exhausted, clear it
swapoff -a && swapon -a
```

### Short-term — Reduce memory pressure
```bash
# Drop page cache
echo 1 > /proc/sys/vm/drop_caches

# If a runaway process, identify and kill:
ps aux | sort -k 4 -rn | head -5
kill -9 <PID>
```

### Medium-term — Tune OOM behaviour
```bash
# Protect critical processes from OOM killer
echo -1000 > /proc/<PID>/oom_score_adj

# Increase swap (temporary)
fallocate -l 4G /swapfile && chmod 600 /swapfile
mkswap /swapfile && swapon /swapfile
```

## Verification Steps
1. Verify restarted service is active: `systemctl is-active <service-name>`
2. Confirm host available memory is healthy: `free -m | awk '/Mem:/ {print $7}'` (should be > 20% total)
3. Check `dmesg -T | grep -i oom` shows no new OOM events after restart.
4. Monitor service RSS memory trend for 15 minutes to ensure no runaway leak.

## Root Cause Investigation
- Check application memory leak: heap dumps, profiler
- Review recent deployments for memory regressions
- Evaluate pod/container resource limits (if Kubernetes)

## Prevention
- Set memory limits on all containerised services
- Alert at 80% RAM utilisation
- Use `earlyoom` daemon for graceful degradation
