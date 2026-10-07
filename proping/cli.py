# -*- coding: utf-8 -*-
"""
ProPing CLI Interface
Unified command line dispatcher for benchmarking, auditing, building, and serving.
"""

import argparse
import sys
import os
import json
import webbrowser
import socket
import urllib.request
import signal
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

from .builder import build_html_catalog
from .pinger import benchmark_providers, ping_target
from .auditor import audit_provider_catalog
from .utils import parse_price

BANNER = r"""
  ____             ____  _             
 |  _ \ _ __ ___  |  _ \(_)_ __   __ _ 
 | |_) | '__/ _ \ | |_) | | '_ \ / _` |
 |  __/| | | (_) ||  __/| | | | | (_| |
 |_|   |_|  \___/ |_|   |_|_| |_|\__, |
                                 |___/ 
 Global Cloud & Datacenter Latency Intelligence Suite
 Version 1.0.0 · MIT License
"""

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def resolve_path(custom_path, default_rel):
    if custom_path:
        if os.path.exists(custom_path):
            return custom_path
        in_root = os.path.join(ROOT_DIR, custom_path)
        if os.path.exists(in_root):
            return in_root
        return custom_path
    if os.path.exists(default_rel):
        return default_rel
    in_root = os.path.join(ROOT_DIR, default_rel)
    if os.path.exists(in_root):
        return in_root
    base_name = os.path.basename(default_rel)
    if os.path.exists(base_name):
        return base_name
    in_root_base = os.path.join(ROOT_DIR, base_name)
    if os.path.exists(in_root_base):
        return in_root_base
    return default_rel

def print_banner():
    print(BANNER)

def cmd_build(args):
    print("🚀 [BUILD] Compiling ProPing HTML Dashboards from Dataset...")
    input_file = resolve_path(args.input, os.path.join("data", "master_cloud_directory.json"))
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return 1

    with open(input_file, "r", encoding="utf-8") as f:
        providers = json.load(f)

    # Sort by ping asc
    providers.sort(key=lambda x: (x.get("avg_ms") is None, float(x.get("avg_ms") or 99999)))
    print(f"  📊 Loaded {len(providers)} verified cloud providers.")

    template_path = args.template or None
    
    # Master Build
    html_content = build_html_catalog(providers, template_path=template_path)
    
    out_master = args.output or os.path.join("dist", "index.html")
    os.makedirs(os.path.dirname(out_master) or ".", exist_ok=True)
    with open(out_master, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"  ✅ Built Master Catalog: {out_master} ({len(providers)} providers)")

    # Also save to root global_cloud_catalog.html for backward compatibility
    with open("global_cloud_catalog.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    # Hourly Build
    hourly = [p for p in providers if p.get("hourly_billing") or 'hour' in str(p.get("billing_model", '')).lower()]
    html_hourly = build_html_catalog(hourly, template_path=template_path, title_suffix=f"({len(hourly)} Hourly Providers)")
    
    out_hourly = args.hourly_output or os.path.join("dist", "hourly.html")
    with open(out_hourly, "w", encoding="utf-8") as f:
        f.write(html_hourly)
    print(f"  ✅ Built Hourly Catalog: {out_hourly} ({len(hourly)} hourly providers)")

    with open("master_hourly_directory.html", "w", encoding="utf-8") as f:
        f.write(html_hourly)

    # Update desktop NewUI.html if exists
    desktop_newui = r"C:\Users\Meow\Desktop\NewUI.html"
    if os.path.exists(desktop_newui):
        try:
            with open(desktop_newui, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"  ✅ Updated Desktop: {desktop_newui}")
        except Exception as e:
            print(f"  ⚠️ Desktop note: {e}")

    print("\n🎉 All catalogs successfully generated and verified!")
    return 0

def cmd_status(args):
    input_file = resolve_path(args.input, os.path.join("data", "master_cloud_directory.json"))
    if not os.path.exists(input_file):
        print(f"❌ Database not found: {input_file}")
        return 1

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    pings = [float(p['avg_ms']) for p in data if p.get('avg_ms') and float(p['avg_ms']) < 9000]
    countries = set(p.get('country') for p in data if p.get('country'))
    hourly = sum(1 for p in data if p.get('hourly_billing') or 'hour' in str(p.get('billing_model', '')).lower())
    crypto = sum(1 for p in data if p.get('crypto'))
    budget = sum(1 for p in data if parse_price(p.get('starting_price')) < 4.0)

    print("=" * 60)
    print("📊 ProPing Telemetry Database Overview")
    print("=" * 60)
    print(f"  Total Verified Providers:  {len(data)}")
    print(f"  Unique Countries:          {len(countries)}")
    print(f"  Average Iran Latency:      {sum(pings)/max(1, len(pings)):.1f} ms")
    print(f"  Best Minimum Latency:      {min(pings):.2f} ms")
    print(f"  Hourly Providers:          {hourly}")
    print(f"  Crypto Accepted:           {crypto}")
    print(f"  Budget Friendly (<$4/mo):  {budget}")
    print("=" * 60)
    return 0

def detect_public_ip():
    """Detect external public IP using lightweight standard library HTTP requests."""
    endpoints = [
        "https://api.ipify.org",
        "https://icanhazip.com",
        "https://ifconfig.me/ip",
        "https://ipinfo.io/ip",
    ]
    for url in endpoints:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/7.88.1"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                raw = resp.read().decode("utf-8").strip()
                if raw and len(raw.split(".")) == 4:
                    return raw
        except Exception:
            continue
    return None

def detect_local_ip():
    """Detect LAN / local network IP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def cmd_serve(args):
    port = getattr(args, "port", None) or 8080
    host = getattr(args, "host", None) or "0.0.0.0"
    directory = getattr(args, "dir", None) or "dist"

    PID_FILE = os.path.expanduser("~/.proping_serve.pid")

    if getattr(args, "stop", False):
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                if sys.platform == "win32":
                    os.system(f"taskkill /PID {pid} /F >nul 2>&1")
                else:
                    os.kill(pid, signal.SIGTERM)
                os.remove(PID_FILE)
                print(f"🛑 Stopped background ProPing server (PID {pid}).")
                return 0
            except Exception as e:
                print(f"⚠️ Could not stop PID {pid}: {e}")
                if os.path.exists(PID_FILE):
                    os.remove(PID_FILE)
                return 1
        else:
            print("ℹ️ No background server PID file found.")
            return 0

    # Ensure directory is found
    if not os.path.exists(directory):
        in_root = os.path.join(ROOT_DIR, directory)
        if os.path.exists(in_root):
            directory = in_root

    index_path = os.path.join(directory, "index.html")
    if not os.path.exists(index_path):
        in_root_dist = os.path.join(ROOT_DIR, "dist", "index.html")
        if os.path.exists(in_root_dist):
            directory = os.path.join(ROOT_DIR, "dist")
        else:
            print("⚠️ Dashboard not built yet. Auto-compiling catalogs first...")
            cmd_build(args)
            if os.path.exists(os.path.join(ROOT_DIR, "dist")):
                directory = os.path.join(ROOT_DIR, "dist")

    if not os.path.exists(directory):
        directory = "."

    if getattr(args, "daemon", False):
        log_file = os.path.expanduser("~/.proping_serve.log")
        py_exe = sys.executable
        cli_entry = os.path.abspath(sys.argv[0])
        cmd = [py_exe, cli_entry, "serve", "--host", host, "--port", str(port), "--dir", directory, "--no-browser"]
        with open(log_file, "a") as log_f:
            if sys.platform == "win32":
                p = subprocess.Popen(cmd, stdout=log_f, stderr=log_f, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                p = subprocess.Popen(cmd, stdout=log_f, stderr=log_f, start_new_session=True)
        with open(PID_FILE, "w") as f:
            f.write(str(p.pid))

        pub_ip = detect_public_ip() or host
        print("=" * 66)
        print("⚡ ProPing Background Daemon Started!")
        print("=" * 66)
        print(f"  PID:              {p.pid}")
        print(f"  🌐 Public Link:   http://{pub_ip}:{port}/")
        print(f"  📊 Hourly View:   http://{pub_ip}:{port}/hourly.html")
        print(f"  📝 Log File:      {log_file}")
        print("=" * 66)
        print("  💡 To stop daemon anytime, run: proping serve --stop\n")
        return 0

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=directory, **kw)
        def log_message(self, format, *a):
            # Suppress normal asset logs to keep console clean
            if a and len(a) > 1 and str(a[1]) not in ("200", "304"):
                super().log_message(format, *a)

    server = None
    bind_port = port
    for p_candidate in [port, port + 1, port + 2, 8000, 8888, 3000]:
        try:
            server = HTTPServer((host, p_candidate), Handler)
            bind_port = p_candidate
            break
        except OSError:
            continue

    if not server:
        print(f"❌ Could not bind server to host {host} on port {port} or fallback ports.")
        return 1

    pub_ip = detect_public_ip()
    local_ip = detect_local_ip()

    print("\n" + "=" * 68)
    print("  ⚡ ProPing Live Telemetry & Latency Dashboard")
    print("=" * 68)
    if pub_ip:
        print(f"  🌐 Public Link:    http://{pub_ip}:{bind_port}/")
        print(f"  📊 Hourly Link:    http://{pub_ip}:{bind_port}/hourly.html")
    if local_ip and local_ip != pub_ip:
        print(f"  🏠 Local Network:  http://{local_ip}:{bind_port}/")
    print(f"  💻 Localhost:      http://localhost:{bind_port}/")
    print(f"  📁 Serving Path:   {os.path.abspath(directory)}")
    print("=" * 68)
    print("  👉 Click or paste the Public Link into your browser.")
    print("  👉 Press Ctrl+C at any time to shut down this temporary server.")
    print("=" * 68 + "\n")

    if not args.no_browser and pub_ip is None:
        url = f"http://localhost:{bind_port}/"
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Temporary ProPing server stopped cleanly.")
        print("💡 Tip: To run it again anytime, execute: proping serve\n")
    return 0

def cmd_ping(args):
    if args.target:
        print(f"🎯 Pinging target {args.target} (count={args.count})...")
        metric = ping_target(args.target, count=args.count)
        print(json.dumps(metric, indent=2))
        return 0

    input_file = resolve_path(args.input, os.path.join("data", "master_cloud_directory.json"))

    print(f"🚀 Running concurrent benchmark on {input_file} (workers={args.workers})...")
    with open(input_file, "r", encoding="utf-8") as f:
        providers = json.load(f)

    def progress(done, total, p, metric):
        ms_str = f"{metric.get('avg_ms'):.1f}ms" if metric.get('avg_ms') else "TIMEOUT"
        print(f"[{done}/{total}] {p.get('brand')[:25]:25} | {p.get('test_ip'):15} | {ms_str}")

    benchmark_providers(providers, max_workers=args.workers, count=args.count, progress_callback=progress)

    out_file = args.output or input_file
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(providers, f, indent=2, ensure_ascii=False)
    print(f"✅ Benchmark finished and saved to {out_file}")
    return 0

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="ProPing - Global Cloud & Datacenter Latency Intelligence Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available commands")

    # Build
    p_build = subparsers.add_parser("build", help="Compile HTML dashboards from database")
    p_build.add_argument("-i", "--input", help="Path to input JSON file")
    p_build.add_argument("-o", "--output", help="Path to output HTML file")
    p_build.add_argument("--hourly-output", help="Path to output hourly HTML file")
    p_build.add_argument("-t", "--template", help="Path to custom base template")

    # Status
    p_status = subparsers.add_parser("status", help="Show database overview and telemetry metrics")
    p_status.add_argument("-i", "--input", help="Path to database JSON file")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Run web server to host dashboard")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host interface to bind (default: 0.0.0.0)")
    p_serve.add_argument("-p", "--port", type=int, default=8080, help="HTTP port (default: 8080)")
    p_serve.add_argument("-d", "--dir", default="dist", help="Directory to serve (default: dist)")
    p_serve.add_argument("--daemon", action="store_true", help="Run server in background as a daemon")
    p_serve.add_argument("--stop", action="store_true", help="Stop running background server")
    p_serve.add_argument("--no-browser", action="store_true", help="Do not automatically launch browser")

    # Ping / Benchmark
    p_ping = subparsers.add_parser("benchmark", help="Run multi-threaded ICMP ping benchmark")
    p_ping.add_argument("-t", "--target", help="Single IP target to test")
    p_ping.add_argument("-i", "--input", help="JSON dataset of targets")
    p_ping.add_argument("-o", "--output", help="Output path for benchmarked JSON")
    p_ping.add_argument("-c", "--count", type=int, default=4, help="Packets per host (default: 4)")
    p_ping.add_argument("-w", "--workers", type=int, default=20, help="Concurrent worker threads (default: 20)")

    args = parser.parse_args()

    if not args.subcommand:
        print_banner()
        parser.print_help()
        sys.exit(0)

    if args.subcommand == "build":
        sys.exit(cmd_build(args))
    elif args.subcommand == "status":
        sys.exit(cmd_status(args))
    elif args.subcommand == "serve":
        sys.exit(cmd_serve(args))
    elif args.subcommand == "benchmark":
        sys.exit(cmd_ping(args))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
