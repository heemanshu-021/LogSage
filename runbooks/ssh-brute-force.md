---
title: "SSH Brute Force / Failed Login Response"
slug: ssh-brute-force
id: RB-004
tags: sshd, brute-force, security, authentication, intrusion
severity: high
illustrative: true
---

> **ILLUSTRATIVE RUNBOOK** — This runbook is provided as a reference template.
> Adapt thresholds and IP blocking tools to your specific environment before use.

# SSH Brute Force / Failed Login Response

## Symptoms
- Repeated `Failed password for invalid user` in auth.log
- `sshd` logging hundreds of attempts per minute
- Unusual source IPs in `/var/log/auth.log`

## Possible Causes
1. **Automated botnet credential stuffing against standard SSH port (22)**
2. **Exposed bastion host without IP whitelisting or fail2ban rules**
3. **Compromised developer credentials or outdated password policy**
4. **Internal rogue process attempting automated lateral movement**

## Investigation Steps

1. **Count failed attempts by source IP:**
   ```bash
   grep "Failed password" /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -20
   ```

2. **Check if any succeeded:**
   ```bash
   grep "Accepted" /var/log/auth.log | tail -20
   ```

3. **Active sessions:**
   ```bash
   who
   last | head -20
   ss -tnp | grep ':22'
   ```

## Remediation

### Block attacking IPs immediately
```bash
# UFW
ufw deny from <attacking-IP> to any

# iptables
iptables -A INPUT -s <attacking-IP> -j DROP

# Using fail2ban (recommended)
fail2ban-client set sshd banip <attacking-IP>
```

### If a breach is suspected
```bash
# Lock all non-essential accounts
for user in $(awk -F: '$3 >= 1000 {print $1}' /etc/passwd | grep -v youradmin); do
  usermod -L $user
done

# Review recently modified files
find / -mmin -60 -type f 2>/dev/null | grep -v /proc | head -50
```

## Verification Steps
1. Verify attacker IP packets are dropped: `iptables -L -n -v | grep <attacking-IP>`
2. Confirm failed login rate returns to baseline (< 5/min): `grep "Failed password" /var/log/auth.log | tail -20`
3. Check fail2ban status: `fail2ban-client status sshd`
4. Verify authorized users can still connect successfully via SSH keys.

## Hardening Steps
- Disable password auth: `PasswordAuthentication no` in `/etc/ssh/sshd_config`
- Restrict to specific IPs via `AllowUsers user@trusted-ip`
- Install and configure `fail2ban`
- Change SSH port from 22 to a non-standard port

## Escalation
If any `Accepted` login from the attacking IP range, escalate to Security Incident immediately.
