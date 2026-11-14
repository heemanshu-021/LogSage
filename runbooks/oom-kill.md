---
title: "Out of Memory (OOM) Kill Response"
slug: oom-kill
tags: kernel, oom, memory, linux, process
severity: critical
---

# Out of Memory Kill Response

## Symptoms
- `kernel: Out of memory: Kill process` in syslog
- `oom-kill:constraint=CONSTRAINT_NONE` kernel messages
- Service unexpectedly exits / restarts

## Immediate Triage

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

## Root Cause Investigation
- Check application memory leak: heap dumps, profiler
- Review recent deployments for memory regressions
- Evaluate pod/container resource limits (if Kubernetes)

## Prevention
- Set memory limits on all containerised services
- Alert at 80% RAM utilisation
- Use `earlyoom` daemon for graceful degradation
