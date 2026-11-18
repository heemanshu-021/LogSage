---
title: "HDFS Block Corruption Recovery"
slug: hdfs-block-corruption
id: RB-005
tags: hdfs, block, corruption, dfs
severity: high
illustrative: true
---

> **ILLUSTRATIVE RUNBOOK** — This runbook is provided as a reference template.
> Adapt HDFS paths and cluster commands to your specific environment before use.

# HDFS Block Corruption Recovery

## Symptoms
- `BLOCK* NameSystem.markBlockAsCorrupt` in NameNode logs
- `IOException in DataXceiver` for a specific block ID
- Files return `ChecksumException` on read

## Possible Causes
1. **Underlying DataNode hardware bad sectors or disk controller faults**
2. **Network transmission corruption during block replication pipeline**
3. **Abrupt DataNode power off or kernel panic mid-block-write**
4. **DataNode process OOM kill or unclean JVM shutdown while flushes pending**

## Investigation Steps

1. **Identify the corrupted block:**
   ```bash
   hdfs fsck / -list-corruptfileblocks 2>&1 | head -50
   ```

2. **Find which DataNodes hold the block:**
   ```bash
   hdfs fsck /path/to/file -files -blocks -locations
   ```

3. **Check DataNode disk health:**
   ```bash
   hdfs dfsadmin -report | grep -A 5 "Name:"
   ```

## Remediation

### Option A — Re-replicate from healthy replica
```bash
# Force re-replication by temporarily reducing replication factor then restoring
hdfs dfs -setrep -w 1 /path/to/file
hdfs dfs -setrep -w 3 /path/to/file
```

### Option B — Delete and restore from backup
```bash
hdfs dfs -rm /path/to/corrupt/file
# Restore from backup (adjust path)
hdfs dfs -copyFromLocal /backup/path/file /path/to/restore
```

### Option C — Trigger fsck repair
```bash
hdfs fsck /path/to/file -move   # moves corrupt blocks to /lost+found
```

## Verification Steps
1. Run HDFS fsck to verify corrupt blocks count is 0: `hdfs fsck / -list-corruptfileblocks`
2. Check replication status: `hdfs dfsadmin -report | grep "Under replicated"`
3. Confirm file can be read without ChecksumException: `hdfs dfs -text /path/to/file > /dev/null`
4. Verify NameNode web UI displays cluster health as HEALTHY.

## Prevention
- Ensure at least 3× replication factor for critical data
- Monitor `dfs.datanode.failed.volumes.tolerated` config
- Enable block scanner: `dfs.block.scanner.volume.bytes.per.second`

## Escalation
If >5% of blocks are corrupt, declare a P1 incident and page the on-call HDFS team.
