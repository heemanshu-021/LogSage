import { useState } from 'react'
import CommandBlock from '../components/CommandBlock'

export default function RunbooksPage({ apiUrl }) {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState('ALL')

  const runbooksCatalog = [
    {
      id: 'RB-005',
      slug: 'hdfs-block-corruption',
      category: 'STORAGE',
      title: 'HDFS Block Corruption Recovery',
      severity: 'CRITICAL',
      symptoms: [
        'BLOCK* NameSystem.markBlockAsCorrupt in NameNode logs',
        'IOException in DataXceiver for specific block ID',
        'Files return ChecksumException upon client read',
      ],
      description:
        'Standard operational remediation procedure when storage blocks suffer disk checksum mismatch or replication failure across Hadoop DataNodes.',
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
      id: 'RB-002',
      slug: 'oom-kill',
      category: 'MEMORY',
      title: 'JVM Heap Exhaustion & OOM Triage',
      severity: 'CRITICAL',
      symptoms: [
        'java.lang.OutOfMemoryError: Java heap space',
        'Linux kernel Out of memory: Kill process (dmesg)',
        'Garbage collection pauses exceeding 10 seconds',
      ],
      description:
        'Triage steps to capture heap dump artifacts, identify memory leaks, and tune container memory bounds before restarting JVM services.',
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
      symptoms: [
        'ConnectionPoolTimeoutException: Timeout waiting for idle connection',
        'Active connection count reaching 100% of max_connections',
        'Slow database queries blocking connection return',
      ],
      description:
        'Diagnose abandoned connections, inspect slow running queries on Postgres/MySQL, and gracefully scale connection pool size.',
      commands: [
        {
          desc: '1. Inspect active connection states and lock status:',
          cmd: 'psql -U postgres -c "SELECT pid, state, age(clock_timestamp(), query_start), query FROM pg_stat_activity WHERE state != \'idle\';"',
        },
        {
          desc: '2. Terminate hung queries running for over 5 minutes:',
          cmd: 'psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state != \'idle\' AND query_start < NOW() - INTERVAL \'5 minutes\';"',
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
      symptoms: [
        'Filesystem /var/log reaches 98% utilization',
        'No space left on device error during write',
        'DataNode refuses new block writes due to volume fill',
      ],
      description:
        'Locate unrotated log files, purge aged archives safely without dropping file handles, and verify mount capacity.',
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
          cmd: 'lsof | grep "(deleted)" | awk \'{print $2}\' | xargs -r kill -HUP',
        },
      ],
    },
    {
      id: 'RB-006',
      slug: 'network-timeout',
      category: 'NETWORK',
      title: 'Inter-Node Network Timeout & Packet Drop',
      severity: 'MEDIUM',
      symptoms: [
        'SocketTimeoutException during RPC call',
        'Connection reset by peer between DataNodes',
        'TCP retransmission spikes on cluster interface',
      ],
      description:
        'Validate MTU configuration, check packet drops across switch interfaces, and verify MTU jumbo frames.',
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
      symptoms: [
        'Failed password for invalid user in /var/log/auth.log',
        'Over 50 authentication failures per minute from single IP',
        'PAM authentication flood',
      ],
      description:
        'Detect attacking IPs from authentication logs, ban host via fail2ban/iptables, and enforce key-only authentication.',
      commands: [
        {
          desc: '1. Extract top attacking IP addresses from auth log:',
          cmd: 'grep "Failed password" /var/log/auth.log | awk \'{print $(NF-3)}\' | sort | uniq -c | sort -nr | head -10',
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
      if (!titleMatch && !descMatch && !symptomMatch) return false
    }
    return true
  })

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <span className="page-tag">OPERATIONAL KNOWLEDGE BASE</span>
          <h1 className="page-title">Runbook Library</h1>
          <p className="page-desc">
            Standard operating procedures with verified CLI commands. LogSage automatically
            matches these runbooks to anomalous log incidents using semantic search.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-card filter-card">
        <div className="filter-row">
          <div className="search-box">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              className="search-input-field"
              placeholder="Search runbooks by keyword (e.g. corruption, heap, timeout)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                className="clear-search-btn"
                onClick={() => setSearchQuery('')}
              >
                ✕
              </button>
            )}
          </div>

          <div className="pill-group">
            <span className="pill-group-label">Category:</span>
            {['ALL', 'STORAGE', 'MEMORY', 'DATABASE', 'DISK', 'NETWORK', 'SECURITY'].map(
              (cat) => (
                <button
                  key={cat}
                  className={`filter-pill ${activeCategory === cat ? 'active' : ''}`}
                  onClick={() => setActiveCategory(cat)}
                >
                  {cat}
                </button>
              )
            )}
          </div>
        </div>
      </div>

      {/* Runbook Cards */}
      <div className="runbooks-grid">
        {filteredRunbooks.map((rb) => (
          <div key={rb.id} className="glass-card runbook-catalog-card">
            <div className="runbook-catalog-top">
              <div className="runbook-badges">
                <span className="runbook-id-badge">{rb.id}</span>
                <span className={`badge badge-${rb.severity.toLowerCase()}`}>
                  {rb.severity}
                </span>
                <span className="category-tag">{rb.category}</span>
              </div>
            </div>

            <h2 className="runbook-catalog-title">{rb.title}</h2>
            <p className="runbook-catalog-desc">{rb.description}</p>

            <div className="runbook-symptoms-box">
              <span className="symptoms-label">Key Symptoms:</span>
              <ul className="symptoms-list">
                {rb.symptoms.map((sym, i) => (
                  <li key={i}>{sym}</li>
                ))}
              </ul>
            </div>

            <div className="runbook-commands-section">
              <span className="commands-header-label">Remediation Commands (Copy-Paste Ready):</span>
              <div className="commands-list">
                {rb.commands.map((cmdItem, i) => (
                  <CommandBlock
                    key={i}
                    command={cmdItem.cmd}
                    description={cmdItem.desc}
                  />
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
