# -*- coding: utf-8 -*-
"""
ProPing Auditor Engine
Audits cloud & VPS hosting websites, validates package availability,
and filters out dead, parked, or suspended domains.
"""

import requests
import urllib3
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

ENTERPRISE_PROVIDERS = {
    'digitalocean.com', 'linode.com', 'vultr.com', 'hetzner.com', 'hetzner.cloud',
    'ovhcloud.com', 'ovh.com', 'scaleway.com', 'upcloud.com', 'kamatera.com',
    'leaseweb.com', 'contabo.com', 'netcup.eu', 'netcup.de', 'time4vps.com',
    'hostinger.com', 'datapacket.com', 'firstcolo.net', 'serverius.net', 'gthost.com',
    'alexhost.com', 'hosteons.com', 'hosthatch.com', 'sim-networks.com', 'deltahost.com',
    'edisglobal.com', 'hostsailor.com', 'webdock.io', 'spacecore.pro', 'altushost.com',
    'play2go.cloud', 'natro.com', 'guzel.net.tr', 'ilkbyte.com', 'netinternet.com.tr',
    'keyubu.com', 'hostlab.com.tr', 'teknosos.com.tr', 'verigom.com', 'datacasa.com.tr',
    'radore.com', 'comnet.com.tr', 'dgn.com.tr', 'trserverim.com', 'narweb.net'
}

SUSPENDED_SIGNATURES = [
    'account suspended', 'suspendedpage.cgi', 'domain parking', 'parked domain',
    'this domain is parked', 'sedoparking', 'dan.com', 'buy this domain',
    'domain for sale', 'plesk default page', "web server's default page",
    'apache2 ubuntu default page', 'welcome to nginx', 'under construction',
    'site under maintenance', 'default website page'
]

SERVER_KEYWORDS = [
    'vps', 'vds', 'cloud', 'cloud server', 'dedicated', 'dedicated server',
    'compute', 'virtual server', 'bare metal', 'kvm', 'cloud compute'
]

def audit_url(url, timeout=7):
    """
    Checks HTTP responsiveness and scans for server package keywords.
    """
    if not url.startswith('http'):
        url = 'https://' + url

    domain = re.sub(r'^https?://(?:www\.)?', '', url).split('/')[0].lower()

    if domain in ENTERPRISE_PROVIDERS:
        return {
            'domain': domain,
            'status': 'VERIFIED_ENTERPRISE',
            'is_valid': True,
            'reason': 'Whitelisted Tier-1 Infrastructure'
        }

    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, verify=False, allow_redirects=True)
        text_lower = resp.text.lower()

        # Check for parked / suspended signatures
        for sig in SUSPENDED_SIGNATURES:
            if sig in text_lower:
                return {
                    'domain': domain,
                    'status': 'SUSPENDED_PARKED',
                    'is_valid': False,
                    'reason': f'Matched parking signature: {sig}'
                }

        # Check for hosting / cloud keywords
        has_server = any(kw in text_lower for kw in SERVER_KEYWORDS)

        if resp.status_code == 200 and has_server:
            return {
                'domain': domain,
                'status': 'ACTIVE_CLOUD',
                'is_valid': True,
                'reason': '200 OK with server/cloud packages verified'
            }
        elif resp.status_code in [401, 403]:
            # Potential WAF protection
            return {
                'domain': domain,
                'status': 'WAF_PROTECTED',
                'is_valid': True,
                'reason': f'WAF challenge ({resp.status_code})'
            }
        else:
            return {
                'domain': domain,
                'status': 'INSUFFICIENT_EVIDENCE',
                'is_valid': False,
                'reason': f'Status {resp.status_code}, server offerings not confirmed'
            }

    except requests.exceptions.RequestException as e:
        return {
            'domain': domain,
            'status': 'UNREACHABLE',
            'is_valid': False,
            'reason': str(e)[:40]
        }

def audit_provider_catalog(providers, max_workers=25, progress_callback=None):
    """
    Audits a collection of provider dicts in parallel.
    """
    total = len(providers)
    completed = 0
    results = []

    def task(p):
        website = p.get('website') or p.get('domain') or ''
        audit_res = audit_url(website) if website else {'is_valid': True, 'status': 'SKIPPED'}
        return p, audit_res

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(task, p): p for p in providers}
        for fut in as_completed(futures):
            p, res = fut.result()
            completed += 1
            results.append((p, res))
            if progress_callback:
                progress_callback(completed, total, p, res)

    return results
