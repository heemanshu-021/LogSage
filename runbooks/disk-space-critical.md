---
title: "Disk Space Critical Alert Response"
slug: disk-space-critical
tags: disk, storage, linux, capacity, cleanup
severity: high
---

# Disk Space Critical Alert Response

## Symptoms
- `WARNING: Disk usage at 92%` / `CRITICAL: Disk usage at 95%+`
- Application write failures: `No space left on device`
- Log rotation failing

## Immediate Triage

1. **Which partition is full?**
   ```bash
   df -h
   df -ih    # check inodes too
   ```

2. **Find largest directories:**
   ```bash
   du -sh /* 2>/dev/null | sort -rh | head -20
   du -sh /var/log/* | sort -rh | head -10
   ```

3. **Large files:**
   ```bash
   find / -xdev -type f -size +500M 2>/dev/null | sort -k5 -rn
   ```

## Remediation

### Quick wins
```bash
# Clean old logs
journalctl --vacuum-size=500M
find /var/log -name "*.gz" -mtime +7 -delete
find /var/log -name "*.log.*" -mtime +7 -delete

# Clean package cache
apt-get clean          # Debian/Ubuntu
yum clean all          # RHEL/CentOS

# Docker cleanup (if applicable)
docker system prune -f
docker volume prune -f
```

### Application log cleanup
```bash
# Truncate (don't delete) active log files
> /var/log/application/app.log

# Check for open file handles on deleted files
lsof | grep deleted | awk '{print $2}' | xargs -I{} ls -la /proc/{}/fd | grep deleted
```

### Extend storage (cloud)
```bash
# AWS: extend EBS volume then resize filesystem
# (do after volume resize in console)
resize2fs /dev/xvda1    # ext4
xfs_growfs /            # xfs
```

## Prevention
- Alert at 80% (warning) and 90% (critical)
- Implement log rotation with `logrotate`
- Set log retention policies: max 14 days / 10 GB
- Use separate mount points for `/var/log` and application data
