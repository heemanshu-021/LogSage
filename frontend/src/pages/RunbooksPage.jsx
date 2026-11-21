import { useState, useEffect } from 'react'
import CommandBlock from '../components/CommandBlock'

export default function RunbooksPage({ apiUrl: _apiUrl }) {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState('ALL')
  const [activeModalRunbook, setActiveModalRunbook] = useState(null)

  // Close modal on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setActiveModalRunbook(null)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const categories = ['ALL', 'STORAGE', 'MEMORY', 'DATABASE', 'DISK', 'NETWORK', 'SECURITY']

  const runbooksCatalog = [
    {
      id: 'RB-001',
      slug: 'postgres-wal-disk-full',
      category: 'DATABASE',
      title: 'Postgres WAL Disk Full & Replication Lag',
      severity: 'CRITICAL',
      time: '10 min',
      tags: ['PostgreSQL', 'WAL', 'Disk Full', 'Replication'],
      successRate: '99%',
      usesCount: 342,
      description:
        'Emergency procedure when PostgreSQL WAL accumulation exhausts storage volume, halting transaction commits and stalling standby replicas.',
      symptoms: [
        'PANIC: could not locate a valid checkpoint record in pg_wal',
        'FATAL: terminating connection due to administrator command: disk full',
        'archive_command failing continuously with exit code 1',
      ],
      commands: [
        {
          desc: '1. Inspect pg_wal directory size and disk consumption:',
          cmd: 'du -sh $PGDATA/pg_wal',
        },
        {
          desc: '2. Check replication slot lag preventing WAL removal:',
          cmd: "psql -U postgres -c \"SELECT slot_name, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS lag FROM pg_replication_slots;\"",
        },
        {
          desc: '3. Drop stale inactive replication slot if blocking cleanup:',
          cmd: "psql -U postgres -c \"SELECT pg_drop_replication_slot('standby_stale_slot');\"",
        },
        {
          desc: '4. Force immediate checkpoint to recycle archived WAL segments:',
          cmd: 'psql -U postgres -c "CHECKPOINT;"',
        },
      ],
    },
    {
      id: 'RB-002',
      slug: 'oom-kill',
      category: 'MEMORY',
      title: 'JVM Heap Exhaustion & OOM Triage',
      severity: 'CRITICAL',
      time: '12 min',
      tags: ['JVM', 'OOM Killer', 'Heap Dump', 'Memory Leak'],
      successRate: '96%',
      usesCount: 285,
      description:
        'Triage steps to capture heap dump artifacts, identify memory leaks, and tune container memory bounds before restarting JVM services.',
      symptoms: [
        'java.lang.OutOfMemoryError: Java heap space',
        'Linux kernel Out of memory: Kill process (dmesg)',
        'Garbage collection pauses exceeding 10 seconds',
      ],
      commands: [
        {
          desc: '1. Inspect kernel dmesg for OOM killer invocations:',
          cmd: 'dmesg -T | grep -i -E "oom[- ]killer|killed process"',
        },
        {
          desc: '2. Generate on-demand JVM heap dump before restarting:',
          cmd: 'jcmd $(pgrep -f "java") GC.heap_dump /var/log/dumps/heap_dump.hprof',
        },
        {
          desc: '3. Adjust max heap size environment variable (e.g. 4GB to 8GB):',
          cmd: 'export JAVA_OPTS="-Xms4g -Xmx8g -XX:+UseG1GC"',
        },
      ],
    },
    {
      id: 'RB-003',
      slug: 'db-connection-timeout',
      category: 'DATABASE',
      title: 'Database Connection Pool Exhaustion',
      severity: 'HIGH',
      time: '8 min',
      tags: ['PostgreSQL', 'PgBouncer', 'Connection Pool', 'Locks'],
      successRate: '94%',
      usesCount: 189,
      description:
        'Diagnose abandoned connections, inspect slow running queries on Postgres/MySQL, and gracefully scale connection pool size.',
      symptoms: [
        'ConnectionPoolTimeoutException: Timeout waiting for idle connection',
        'Active connection count reaching 100% of max_connections',
        'Slow database queries blocking connection return',
      ],
      commands: [
        {
          desc: '1. Inspect active connection states and lock status:',
          cmd: "psql -U postgres -c \"SELECT pid, state, age(clock_timestamp(), query_start), query FROM pg_stat_activity WHERE state != 'idle';\"",
        },
        {
          desc: '2. Terminate hung queries running for over 5 minutes:',
          cmd: "psql -U postgres -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state != 'idle' AND query_start < NOW() - INTERVAL '5 minutes';\"",
        },
        {
          desc: '3. Temporarily increase pool ceiling on running proxy:',
          cmd: 'systemctl reload pgbouncer',
        },
      ],
    },
    {
      id: 'RB-004',
      slug: 'disk-space-critical',
      category: 'DISK',
      title: 'Disk Space Critical & Log Rotation',
      severity: 'HIGH',
      time: '6 min',
      tags: ['Disk Space', 'Logrotate', 'File Handles', 'Root Volume'],
      successRate: '98%',
      usesCount: 412,
      description:
        'Locate unrotated log files, purge aged archives safely without dropping file handles, and verify mount capacity.',
      symptoms: [
        'Filesystem /var/log reaches 98% utilization',
        'No space left on device error during write',
        'DataNode refuses new block writes due to volume fill',
      ],
      commands: [
        {
          desc: '1. Find top 10 largest log files on root filesystem:',
          cmd: 'du -ah /var/log | sort -rh | head -n 10',
        },
        {
          desc: '2. Force immediate logrotate without waiting for midnight cron:',
          cmd: 'logrotate -f /etc/logrotate.conf',
        },
        {
          desc: '3. Find and release deleted files still held open by processes:',
          cmd: "lsof | grep '(deleted)' | awk '{print $2}' | xargs -r kill -HUP",
        },
      ],
    },
    {
      id: 'RB-005',
      slug: 'hdfs-block-corruption',
      category: 'STORAGE',
      title: 'HDFS Block Corruption Recovery',
      severity: 'CRITICAL',
      time: '15 min',
      tags: ['HDFS', 'Hadoop', 'Checksum', 'DataNode'],
      successRate: '92%',
      usesCount: 124,
      description:
        'Standard operational remediation procedure when storage blocks suffer disk checksum mismatch or replication failure across Hadoop DataNodes.',
      symptoms: [
        'BLOCK* NameSystem.markBlockAsCorrupt in NameNode logs',
        'IOException in DataXceiver for specific block ID',
        'Files return ChecksumException upon client read',
      ],
      commands: [
        {
          desc: '1. Scan and report all corrupted blocks in cluster:',
          cmd: 'hdfs fsck / -list-corruptfileblocks',
        },
        {
          desc: '2. Check replica health and hosting DataNode IPs:',
          cmd: 'hdfs fsck / -files -blocks -locations',
        },
        {
          desc: '3. Re-replicate block from surviving healthy replica:',
          cmd: 'hdfs dfs -setrep -w 3 /data/hdfs_blocks/corrupted_block',
        },
        {
          desc: '4. Move unrecoverable block to /lost+found if replica is permanently dead:',
          cmd: 'hdfs fsck / -move -delete',
        },
      ],
    },
    {
      id: 'RB-006',
      slug: 'network-timeout',
      category: 'NETWORK',
      title: 'Inter-Node Network Timeout & Packet Drop',
      severity: 'MEDIUM',
      time: '12 min',
      tags: ['Networking', 'TCP Retransmit', 'MTU', 'Latency'],
      successRate: '89%',
      usesCount: 95,
      description:
        'Validate MTU configuration, check packet drops across switch interfaces, and verify MTU jumbo frames.',
      symptoms: [
        'SocketTimeoutException during RPC call',
        'Connection reset by peer between DataNodes',
        'TCP retransmission spikes on cluster interface',
      ],
      commands: [
        {
          desc: '1. Test TCP throughput and latency between cluster nodes:',
          cmd: 'iperf3 -c target-datanode.internal -p 5201 -t 10',
        },
        {
          desc: '2. Check for interface drop errors and TCP retransmits:',
          cmd: 'netstat -s | grep -i "retransmit"',
        },
      ],
    },
    {
      id: 'RB-007',
      slug: 'ssh-brute-force',
      category: 'SECURITY',
      title: 'SSH Brute-Force Intrusion Mitigation',
      severity: 'HIGH',
      time: '5 min',
      tags: ['Security', 'SSH', 'Fail2ban', 'Iptables'],
      successRate: '97%',
      usesCount: 520,
      description:
        'Detect attacking IPs from authentication logs, ban host via fail2ban/iptables, and enforce key-only authentication.',
      symptoms: [
        'Failed password for invalid user in /var/log/auth.log',
        'Over 50 authentication failures per minute from single IP',
        'PAM authentication flood',
      ],
      commands: [
        {
          desc: '1. Extract top attacking IP addresses from auth log:',
          cmd: "grep 'Failed password' /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -nr | head -10",
        },
        {
          desc: '2. Drop attacker traffic immediately via iptables:',
          cmd: 'iptables -A INPUT -s 192.0.2.1 -j DROP',
        },
        {
          desc: '3. Reload fail2ban jail to persist firewall rules:',
          cmd: 'fail2ban-client reload',
        },
      ],
    },
    {
      id: 'RB-008',
      slug: 'kubernetes-crashloop',
      category: 'MEMORY',
      title: 'Kubernetes CrashLoopBackOff & Pod Restart Loop',
      severity: 'CRITICAL',
      time: '14 min',
      tags: ['Kubernetes', 'CrashLoopBackOff', 'Pod Restarts', 'CGroup'],
      successRate: '95%',
      usesCount: 310,
      description:
        'Diagnostic workflow for container restart loops, inspecting termination exit codes, OOM events, and probe failures in Kubernetes pods.',
      symptoms: [
        'Kubernetes pod shows CrashLoopBackOff with increasing RESTARTS count',
        'Systemd reports start request repeated too quickly',
        'Application exits with non-zero exit code immediately after startup',
      ],
      commands: [
        {
          desc: '1. Check recent pod status and restart count:',
          cmd: 'kubectl get pods -n default -o wide',
        },
        {
          desc: '2. Inspect termination reason and previous container logs:',
          cmd: 'kubectl logs <pod-name> --previous --tail=100',
        },
        {
          desc: '3. Describe pod events to inspect liveness/readiness probe failures:',
          cmd: 'kubectl describe pod <pod-name>',
        },
        {
          desc: '4. Check if pod was OOMKilled by node cgroup:',
          cmd: "kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.reason}'",
        },
      ],
    },
  ]

  const filteredRunbooks = runbooksCatalog.filter((rb) => {
    if (activeCategory !== 'ALL' && rb.category !== activeCategory) {
      return false
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      const titleMatch = rb.title.toLowerCase().includes(q)
      const descMatch = rb.description.toLowerCase().includes(q)
      const symptomMatch = rb.symptoms.some((s) => s.toLowerCase().includes(q))
      const tagMatch = rb.tags.some((t) => t.toLowerCase().includes(q))
      const catMatch = rb.category.toLowerCase().includes(q)
      const idMatch = rb.id.toLowerCase().includes(q)
      if (!titleMatch && !descMatch && !symptomMatch && !tagMatch && !catMatch && !idMatch) {
        return false
      }
    }
    return true
  })

  return (
    <div className="runbooks-page-root">
      {/* 2 Soft glow orbs behind content */}
      <div className="runbooks-orb runbooks-orb-1" aria-hidden="true" />
      <div className="runbooks-orb runbooks-orb-2" aria-hidden="true" />

      <div className="runbooks-content-layer">
        {/* 1. Top Header */}
        <header className="runbooks-top-header">
          <div className="runbooks-header-left">
            <h1 className="runbooks-title">Runbook Library</h1>
            <p className="runbooks-subtitle">
              Standard operating procedures with verified CLI remediation commands
            </p>
          </div>
          <div className="runbooks-header-right">
            <div className="runbooks-search-wrapper">
              <span className="runbooks-search-icon" aria-hidden="true">
                🔍
              </span>
              <input
                type="text"
                className="runbooks-search-input"
                placeholder="Search runbooks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                aria-label="Search runbooks"
              />
              {searchQuery && (
                <button
                  type="button"
                  className="runbooks-search-clear"
                  onClick={() => setSearchQuery('')}
                  aria-label="Clear search"
                >
                  ✕
                </button>
              )}
            </div>
          </div>
        </header>

        {/* 2. Category Filter Row */}
        <nav className="runbooks-categories-nav" aria-label="Runbook Categories">
          <div className="runbooks-categories-scroll">
            {categories.map((cat) => {
              const isActive = activeCategory === cat
              return (
                <button
                  key={cat}
                  type="button"
                  className={`runbooks-cat-pill ${isActive ? 'active' : ''}`}
                  onClick={() => setActiveCategory(cat)}
                  aria-pressed={isActive}
                >
                  {cat}
                </button>
              )
            })}
          </div>
        </nav>

        {/* 3. Runbook Cards Grid */}
        {filteredRunbooks.length > 0 ? (
          <div className="runbooks-cards-grid">
            {filteredRunbooks.map((rb) => {
              const severityClass = `runbook-badge-${rb.severity.toLowerCase()}`

              return (
                <article key={rb.id} className="runbook-glass-card">
                  {/* Row 1: Badge left (CRITICAL / HIGH / MEDIUM) + Time right */}
                  <div className="runbook-card-row1">
                    <span className={`runbook-badge ${severityClass}`}>{rb.severity}</span>
                    <span className="runbook-time-label">⏱️ {rb.time}</span>
                  </div>

                  {/* Row 2: Title */}
                  <h2 className="runbook-card-title">{rb.title}</h2>

                  {/* Row 3: Description 2 lines */}
                  <p className="runbook-card-desc">{rb.description}</p>

                  {/* Row 4: Tags as small pills */}
                  <div className="runbook-card-tags">
                    {rb.tags.map((tag) => (
                      <span key={tag} className="runbook-tag-pill">
                        {tag}
                      </span>
                    ))}
                  </div>

                  {/* Row 5: Footer - Left: Success rate + Uses count, Right: Use Runbook button */}
                  <div className="runbook-card-footer">
                    <div className="runbook-card-stats">
                      <span>{rb.successRate} success</span>
                      <span className="runbook-stats-dot">·</span>
                      <span>{rb.usesCount} uses</span>
                    </div>
                    <button
                      type="button"
                      className="runbook-use-btn"
                      onClick={() => setActiveModalRunbook(rb)}
                    >
                      Use Runbook
                    </button>
                  </div>
                </article>
              )
            })}
          </div>
        ) : (
          <div className="runbooks-empty-state">
            <div className="runbooks-empty-icon">🔎</div>
            <h3 className="runbooks-empty-title">No runbooks found</h3>
            <p className="runbooks-empty-desc">
              No operational runbooks matched your search &quot;{searchQuery}&quot; in the &apos;
              {activeCategory}&apos; category.
            </p>
            <button
              type="button"
              className="runbook-use-btn"
              onClick={() => {
                setSearchQuery('')
                setActiveCategory('ALL')
              }}
            >
              Reset Filters
            </button>
          </div>
        )}
      </div>

      {/* Interactive Runbook Execution / Detail Modal */}
      {activeModalRunbook && (
        <div
          className="runbook-modal-backdrop"
          onClick={() => setActiveModalRunbook(null)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-runbook-title"
        >
          <div
            className="runbook-modal-card"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="runbook-modal-header">
              <div className="runbook-modal-badges">
                <span className="runbook-modal-id">{activeModalRunbook.id}</span>
                <span
                  className={`runbook-badge runbook-badge-${activeModalRunbook.severity.toLowerCase()}`}
                >
                  {activeModalRunbook.severity}
                </span>
                <span className="runbook-modal-cat">{activeModalRunbook.category}</span>
                <span className="runbook-time-label">⏱️ {activeModalRunbook.time}</span>
              </div>
              <button
                type="button"
                className="runbook-modal-close"
                onClick={() => setActiveModalRunbook(null)}
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            <h2 id="modal-runbook-title" className="runbook-modal-title">
              {activeModalRunbook.title}
            </h2>
            <p className="runbook-modal-desc">{activeModalRunbook.description}</p>

            <div className="runbook-modal-section">
              <h4 className="runbook-modal-section-title">Trigger Symptoms & Anomalies</h4>
              <ul className="runbook-modal-symptoms">
                {activeModalRunbook.symptoms.map((symptom, idx) => (
                  <li key={idx}>{symptom}</li>
                ))}
              </ul>
            </div>

            <div className="runbook-modal-section">
              <h4 className="runbook-modal-section-title">
                Remediation Playbook (Copy &amp; Execute)
              </h4>
              <div className="runbook-modal-commands">
                {activeModalRunbook.commands.map((cmdItem, idx) => (
                  <CommandBlock
                    key={idx}
                    command={cmdItem.cmd}
                    description={cmdItem.desc}
                  />
                ))}
              </div>
            </div>

            <div className="runbook-modal-footer">
              <div className="runbook-card-stats">
                <span>{activeModalRunbook.successRate} historic resolution rate</span>
                <span className="runbook-stats-dot">·</span>
                <span>{activeModalRunbook.usesCount} incident matches</span>
              </div>
              <button
                type="button"
                className="runbook-use-btn"
                onClick={() => setActiveModalRunbook(null)}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
