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

def print_banner():
    print(BANNER)

def cmd_build(args):
    print("🚀 [BUILD] Compiling ProPing HTML Dashboards from Dataset...")
    input_file = args.input or os.path.join("data", "master_cloud_directory.json")
    if not os.path.exists(input_file):
        if os.path.exists("master_cloud_directory.json"):
            input_file = "master_cloud_directory.json"
        else:
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
    input_file = args.input or os.path.join("data", "master_cloud_directory.json")
    if not os.path.exists(input_file):
        input_file = "master_cloud_directory.json"
    
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

def cmd_serve(args):
    port = args.port or 8080
    directory = args.dir or "dist"
    if not os.path.exists(directory):
        directory = "."

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=directory, **kw)

    server = HTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"🌐 [SERVE] Serving ProPing Dashboard on {url}")
    print(f"📁 Root directory: {os.path.abspath(directory)}")
    print("Press Ctrl+C to stop the server.\n")

    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
    return 0

def cmd_ping(args):
    if args.target:
        print(f"🎯 Pinging target {args.target} (count={args.count})...")
        metric = ping_target(args.target, count=args.count)
        print(json.dumps(metric, indent=2))
        return 0

    input_file = args.input or os.path.join("data", "master_cloud_directory.json")
    if not os.path.exists(input_file):
        input_file = "master_cloud_directory.json"

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
    p_serve = subparsers.add_parser("serve", help="Run local web server to preview dashboard")
    p_serve.add_argument("-p", "--port", type=int, default=8080, help="Local HTTP port (default: 8080)")
    p_serve.add_argument("-d", "--dir", default="dist", help="Directory to serve (default: dist)")
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
