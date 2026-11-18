"""
Run DrainParser against actual HDFS records and generate structured outputs.
"""
from pathlib import Path
import json
import sys
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.parser.drain_parser import DrainParser

def main():
    log_path = Path("data/raw/HDFS_2k.log")
    if not log_path.exists():
        raise FileNotFoundError(f"{log_path} does not exist.")

    parser = DrainParser(config_path="ml/parser/parser_config.ini")
    print(f"Loading and parsing records from {log_path}...")

    results = list(parser.parse_file(log_path))
    print(f"Parsed {len(results):,} log lines.")

    # Show examples
    print("\n" + "=" * 80)
    print("EXAMPLES OF RAW MESSAGES AND PARSED TEMPLATES")
    print("=" * 80)

    sample_indices = [0, 1, 2, 8, 9]
    for idx in sample_indices:
        if idx < len(results):
            r = results[idx]
            print(f"\n--- Record #{r.line_id} ---")
            print(f"Raw Message    : {r.raw_message}")
            print(f"Timestamp      : {r.timestamp}")
            print(f"Level / Comp   : [{r.level}] {r.component} (PID: {r.pid})")
            print(f"Event ID       : {r.event_id}")
            print(f"Event Template : {r.event_template}")
            print(f"Block IDs      : {r.block_ids}")
            print(f"Parameters     : {r.parameters}")
            print(f"Parameter Info : {r.parameter_details}")

    # Export to data/processed
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "hdfs_parsed_sample.csv"
    json_path = out_dir / "hdfs_parsed_sample.json"

    DrainParser.to_csv(results, csv_path)
    DrainParser.to_json(results, json_path, indent=2)

    templates = parser.get_templates()
    stats = parser.get_cluster_stats()
    print("\n" + "=" * 80)
    print("PARSING STATISTICS")
    print("=" * 80)
    print(f"Total lines parsed     : {len(results):,}")
    print(f"Unique event templates : {len(templates)}")
    print(f"Output CSV saved to    : {csv_path} ({csv_path.stat().st_size:,} bytes)")
    print(f"Output JSON saved to   : {json_path} ({json_path.stat().st_size:,} bytes)")

    print("\nTop 5 Most Frequent Event Templates:")
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]["size"], reverse=True)
    for event_id, item in sorted_stats[:5]:
        print(f"  [{event_id}] (count={item['size']:,}): {item['template']}")

if __name__ == "__main__":
    main()
