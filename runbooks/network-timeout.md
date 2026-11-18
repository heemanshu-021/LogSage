---
title: "Network Request Timeout Response"
slug: network-timeout
id: RB-007
tags: network, timeout, latency, tcp, http, dns, firewall, connectivity
severity: high
illustrative: true
---

> **ILLUSTRATIVE RUNBOOK** — This runbook is provided as a reference template.
> Adapt addresses, ports, and service names to your specific environment before use.

# Network Request Timeout Response

## Symptoms
- Application logs show `connection timed out`, `read timeout`, `request timeout exceeded`
- HTTP 504 Gateway Timeout or 502 Bad Gateway responses
- `socket.timeout` / `net::ERR_TIMED_OUT` errors in service logs
- Elevated latency metrics in observability dashboards (p99 > SLA threshold)
- Health checks failing intermittently
- DNS resolution taking > 1 second

## Possible Causes
1. **Downstream service overloaded** — target service is processing requests too slowly
2. **Network congestion or packet loss** — physical or virtual network path is saturated
3. **Firewall or security group rule** — silent packet drop instead of TCP RST
4. **DNS resolution failure** — incorrect nameserver or high DNS lookup latency
5. **Connection pool exhaustion** — no free connections available; requests queue until timeout
6. **Wrong timeout configuration** — application timeout set too short for the operation
7. **TLS handshake delay** — expired certificates or slow CA verification
8. **Inter-zone routing issue** — cloud VPC route table misconfiguration

## Investigation Steps

1. **Verify basic reachability to the target host:**
   ```bash
   ping -c 10 <target-host>
   traceroute <target-host>
   mtr --report <target-host>
   ```

2. **Check TCP connectivity on the service port:**
   ```bash
   nc -zv <target-host> <port>              # test TCP connect
   curl -v --connect-timeout 5 http://<target-host>:<port>/health
   ```

3. **Measure DNS resolution time:**
   ```bash
   time nslookup <target-hostname>
   dig @8.8.8.8 <target-hostname>           # test against public DNS
   dig @<internal-dns-ip> <target-hostname> # test against internal DNS
   ```

4. **Check for packet loss:**
   ```bash
   ping -c 100 <target-host> | tail -5
   # Look for packet loss percentage > 0%
   ```

5. **Inspect application timeout configuration:**
   ```bash
   grep -ri "timeout\|connect_timeout\|read_timeout" /etc/<service>/ /app/config/
   ```

6. **Review network interface statistics:**
   ```bash
   ip -s link show <interface>
   # Look for: RX/TX errors, dropped packets
   netstat -s | grep -i "retransmit\|fail\|timeout"
   ss -s     # socket summary
   ```

7. **Check firewall rules:**
   ```bash
   iptables -L -n -v | grep <target-port>
   # Cloud: check security groups and NACLs in the console
   ```

8. **Look at connection pool state:**
   ```bash
   ss -tnp | grep <target-port> | awk '{print $1}' | sort | uniq -c
   # Compare ESTABLISHED vs TIME_WAIT vs CLOSE_WAIT counts
   ```

9. **Review recent deployments and configuration changes:**
   ```bash
   git log --oneline --since="1 hour ago"   # recent code changes
   # Check infrastructure change log / deployment pipeline
   ```

## Remediation

### If the target service is overloaded:
```bash
# Check target service resource usage
ssh <target-host> "uptime; free -h; iostat -x 1 3"
# Scale horizontally if possible, or shed load from upstream
```

### If DNS resolution is the culprit:
```bash
# Restart local DNS resolver
systemctl restart systemd-resolved
# Or add a /etc/hosts override as a temporary workaround:
echo "<ip-address>  <hostname>" >> /etc/hosts
```

### If a firewall rule is blocking traffic (operator-approved):
```bash
# Temporarily open the port for diagnosis (revert afterwards)
iptables -I INPUT 1 -p tcp --dport <port> -j ACCEPT
# Permanently fix via your infrastructure-as-code tooling
```

### If connection pool is exhausted:
```bash
# Restart the application to flush the pool (last resort)
systemctl restart <service-name>
# Long-term: tune pool size in application configuration
```

### If TLS is the bottleneck:
```bash
# Check certificate validity
openssl s_client -connect <target-host>:<port> -servername <hostname> < /dev/null 2>&1 | grep "Verify\|expire"
# Renew certificate if expired
certbot renew --dry-run
```

## Verification Steps
1. Run the failing request again: confirm it returns within SLA
2. Check error rate drops to baseline in observability dashboard
3. Verify p50/p99 latency returns to normal
4. Confirm health check succeeds for 5 consecutive checks

## Escalation
- If packet loss > 1% persists after 15 minutes: escalate to network/infrastructure team
- If the target service is not owned by your team: open an incident with the owning team
- If a cloud provider network issue is suspected: open a support ticket and check status page

## Prevention
- Set explicit, documented timeouts for all outbound network calls
- Implement retry logic with exponential backoff and jitter
- Configure circuit breakers to avoid cascading failures
- Monitor DNS resolution latency with an active probe
- Alert on p99 latency > 2× baseline for 5 consecutive minutes
