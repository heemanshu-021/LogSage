---
title: "Database Connection Timeout Response"
slug: db-connection-timeout
tags: database, connection, timeout, postgresql, mysql, network
severity: critical
---

# Database Connection Timeout Response

## Symptoms
- `Database connection timeout after 30s` repeated in application logs
- `ERROR: could not connect to server: Connection timed out`
- Application returning 500 errors / degraded mode

## Immediate Triage

1. **Is the DB server reachable?**
   ```bash
   ping <db-host>
   telnet <db-host> 5432     # PostgreSQL
   telnet <db-host> 3306     # MySQL
   nc -zv <db-host> 5432
   ```

2. **Connection pool saturation:**
   ```bash
   # PostgreSQL
   psql -h <host> -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
   psql -h <host> -c "SELECT max_conn, used FROM (SELECT setting::int max_conn FROM pg_settings WHERE name='max_connections') t, (SELECT count(*) used FROM pg_stat_activity) s;"
   ```

3. **Check DB server load:**
   ```bash
   ssh <db-host> "uptime; free -h; df -h"
   ```

## Remediation

### If DB server is unreachable — network issue
```bash
# Check firewall rules
iptables -L -n | grep <port>
ufw status

# Check security group rules (AWS)
aws ec2 describe-security-groups --group-ids <sg-id>

# Restart network interface if needed
ip link set eth0 down && ip link set eth0 up
```

### If connection pool exhausted
```bash
# PostgreSQL — terminate idle connections
psql -h <host> -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '5 minutes';"

# Restart application connection pool
systemctl restart <app-service>
```

### If DB server overloaded
```bash
# PostgreSQL — check slow queries
psql -h <host> -c "SELECT pid, now()-query_start AS duration, query FROM pg_stat_activity WHERE state='active' ORDER BY duration DESC LIMIT 10;"

# Kill long-running queries
psql -h <host> -c "SELECT pg_cancel_backend(<pid>);"
```

## Failover (if primary is down)
```bash
# Promote standby (PostgreSQL streaming replication)
pg_ctl promote -D /var/lib/postgresql/data

# Update application connection string to standby
systemctl restart <app-service>
```

## Prevention
- Set connection pool limits (pgBouncer recommended)
- Implement retry logic with exponential backoff in application
- Configure `max_connections` and `idle_in_transaction_session_timeout`
- Use read replicas for read-heavy workloads
- Alert on `pg_stat_activity` connection count > 80% of max
