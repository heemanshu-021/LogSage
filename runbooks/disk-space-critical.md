---
title: "Disk Space Critical Alert Response"
slug: disk-space-critical
id: RB-003
tags: disk, storage, linux, capacity, cleanup
severity: high
illustrative: true
---

> **ILLUSTRATIVE RUNBOOK** — This runbook is provided as a reference template.
> Adapt paths and cleanup commands to your specific environment before use.

# Disk Space Critical Alert Response

## Symptoms
- `WARNING: Disk usage at 92%` / `CRITICAL: Disk usage at 95%+`
- Application write failures: `No space left on device`
- Log rotation failing

## Possible Causes
1. **Uncompressed or unrotated application logs filling `/var/log`**
2. **Accumulated docker images, containers, and dangling volumes**
3. **Core dumps or crash files generated in `/tmp` or `/var/crash`**
4. **Deleted files still held open by running processes preventing inode reclamation**
5. **Database WAL or transaction log accumulation due to backup stalls**

## Investigation Steps

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

## Verification Steps
1. Verify partition usage is below threshold (< 80%): `df -h`
2. Check inode availability: `df -i`
3. Confirm application write operations succeed: `touch /var/log/test-write && rm /var/log/test-write`
4. Confirm monitoring alert state transitions from CRITICAL to OK.

## Prevention
- Alert at 80% (warning) and 90% (critical)
- Implement log rotation with `logrotate`
- Set log retention policies: max 14 days / 10 GB
- Use separate mount points for `/var/log` and application data
