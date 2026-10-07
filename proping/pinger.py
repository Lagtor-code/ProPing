# -*- coding: utf-8 -*-
"""
ProPing Benchmark Engine
High-performance concurrent ICMP latency and jitter measurement module.
"""

import subprocess
import platform
import re
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

def ping_target(ip, count=4, timeout_sec=2):
    """
    Ping a single IP target and compute min, avg, max, jitter, and packet loss.
    Cross-platform support for Windows, Linux, and macOS.
    """
    is_win = platform.system().lower() == "windows"
    
    if is_win:
        cmd = ["ping", "-n", str(count), "-w", str(int(timeout_sec * 1000)), ip]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(timeout_sec), ip]

    try:
        start_t = time.time()
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout_sec * count + 2)
        out = res.stdout

        # Packet Loss
        loss_match = re.search(r'(\d+)%\s*(?:packet\s*)?loss', out, re.I)
        loss_pct = float(loss_match.group(1)) if loss_match else (0.0 if res.returncode == 0 else 100.0)

        # Latency Extraction
        times = []
        if is_win:
            # e.g. "Reply from 1.1.1.1: bytes=32 time=35ms TTL=54" or "time<1ms"
            for m in re.finditer(r'time[=<]?\s*([0-9.]+)\s*ms', out, re.I):
                times.append(float(m.group(1)))
        else:
            # e.g. "64 bytes from 1.1.1.1: icmp_seq=1 ttl=54 time=35.2 ms"
            for m in re.finditer(r'time=([0-9.]+)\s*ms', out, re.I):
                times.append(float(m.group(1)))

        if times:
            min_ms = round(min(times), 2)
            max_ms = round(max(times), 2)
            avg_ms = round(sum(times) / len(times), 2)
            
            # Jitter calculation (average difference between consecutive packets)
            if len(times) > 1:
                diffs = [abs(times[i] - times[i-1]) for i in range(1, len(times))]
                jitter_ms = round(sum(diffs) / len(diffs), 2)
            else:
                jitter_ms = 0.0

            status = "ONLINE"
        else:
            min_ms = None
            max_ms = None
            avg_ms = None
            jitter_ms = None
            status = "TIMEOUT" if loss_pct == 100.0 else "UNREACHABLE"

        return {
            "ip": ip,
            "status": status,
            "avg_ms": avg_ms,
            "min_ms": min_ms,
            "max_ms": max_ms,
            "jitter_ms": jitter_ms,
            "loss_pct": loss_pct,
            "samples": len(times),
            "protocol": "ICMP",
            "tested_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }

    except subprocess.TimeoutExpired:
        return {
            "ip": ip,
            "status": "TIMEOUT",
            "avg_ms": None,
            "min_ms": None,
            "max_ms": None,
            "jitter_ms": None,
            "loss_pct": 100.0,
            "samples": 0,
            "protocol": "ICMP",
            "tested_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }
    except Exception as e:
        return {
            "ip": ip,
            "status": f"ERROR: {str(e)[:30]}",
            "avg_ms": None,
            "min_ms": None,
            "max_ms": None,
            "jitter_ms": None,
            "loss_pct": 100.0,
            "samples": 0,
            "protocol": "ICMP",
            "tested_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }

def benchmark_providers(providers, max_workers=20, count=4, progress_callback=None):
    """
    Concurrently benchmarks a list of provider objects containing 'test_ip'.
    Updates each provider in-place with network metrics.
    """
    total = len(providers)
    completed = 0

    def task(p):
        ip = p.get('test_ip')
        if not ip:
            return p, {"status": "NO_IP"}
        metric = ping_target(ip, count=count)
        return p, metric

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(task, p): p for p in providers}
        for fut in as_completed(futures):
            p, metric = fut.result()
            completed += 1
            if metric.get("avg_ms") is not None:
                p["avg_ms"] = metric["avg_ms"]
                p["min_ms"] = metric["min_ms"]
                p["max_ms"] = metric["max_ms"]
                p["jitter_ms"] = metric["jitter_ms"]
                p["loss_pct"] = metric["loss_pct"]
                p["status"] = metric["status"]
            if progress_callback:
                progress_callback(completed, total, p, metric)

    return providers
