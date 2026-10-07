# -*- coding: utf-8 -*-
"""
ProPing Dashboard Builder
Compiles verified cloud datasets into standalone, zero-dependency, ultra-modern HTML/CSS/JS catalogs.
Grounded in the NewUI design system architecture.
"""

import os
import re
import json
from collections import Counter
from .utils import get_iso, parse_price, clean_record

DEFAULT_TEMPLATE_PATH = r"C:\Users\Meow\Desktop\NewUI.html"

def build_html_catalog(providers, template_path=None, title_suffix=""):
    """
    Compiles a list of cloud providers into a complete standalone HTML dashboard.
    """
    repo_template = os.path.join(os.path.dirname(__file__), "..", "templates", "newui_template.html")
    if template_path is None or not os.path.exists(template_path):
        if os.path.exists(repo_template):
            template_path = repo_template
        elif os.path.exists(DEFAULT_TEMPLATE_PATH):
            template_path = DEFAULT_TEMPLATE_PATH
        elif os.path.exists("NewUI.html"):
            template_path = "NewUI.html"
        elif os.path.exists(os.path.join(os.path.dirname(__file__), "..", "dist", "index.html")):
            template_path = os.path.join(os.path.dirname(__file__), "..", "dist", "index.html")
        else:
            raise FileNotFoundError("Could not locate NewUI base template.")

    with open(template_path, 'r', encoding='utf-8') as f:
        template_text = f.read()

    # 1. Extract Head & Header part (everything up to <aside class="app-sidebar")
    sidebar_marker = '<aside class="app-sidebar"'
    sidebar_idx = template_text.find(sidebar_marker)
    if sidebar_idx == -1:
        raise ValueError("Could not find <aside class=\"app-sidebar\" in template!")

    head_part = template_text[:sidebar_idx]
    
    # Clean records
    providers = [clean_record(dict(p)) for p in providers]

    total_count = len(providers)
    unique_countries = sorted(set(p.get('country') for p in providers if p.get('country')))
    unique_countries_count = len(unique_countries)

    # Update page title in head
    head_part = re.sub(
        r'<title>.*?</title>',
        f'<title>ProPing — Global Cloud &amp; Datacenter Telemetry ({total_count} Verified Providers {title_suffix})</title>',
        head_part
    )

    # Update header subtitle counts
    head_part = re.sub(
        r'<span>\d+ Verified Commercial Providers across \d+ Countries</span>',
        f'<span>{total_count} Verified Commercial Providers across {unique_countries_count} Countries</span>',
        head_part
    )

    # 2. Compute Metrics for Sidebar & Heroes
    online_pings = [float(p['avg_ms']) for p in providers if p.get('avg_ms') and float(p['avg_ms']) < 9000]
    avg_ping = round(sum(online_pings) / max(1, len(online_pings)), 1) if online_pings else 0.0
    min_ping = round(min(online_pings), 2) if online_pings else 0.0

    # Category counts
    cnt_all = total_count
    cnt_sub50 = sum(1 for p in providers if (float(p.get('avg_ms') or 9999)) < 50)
    cnt_lowlat = sum(1 for p in providers if 50 <= float(p.get('avg_ms') or 9999) < 80)
    cnt_stdeu = sum(1 for p in providers if 80 <= float(p.get('avg_ms') or 9999) < 120)
    cnt_hourly = sum(1 for p in providers if p.get('hourly_billing') or 'hour' in str(p.get('billing_model', '')).lower())
    cnt_crypto = sum(1 for p in providers if p.get('crypto'))
    cnt_budget = sum(1 for p in providers if parse_price(p.get('starting_price')) < 4.0)
    cnt_ddos = sum(1 for p in providers if 'ddos' in p.get('brand', '').lower() or 'ddos' in str(p.get('tags', '')).lower())
    cnt_privacy = sum(1 for p in providers if 'privacy' in str(p.get('tags', '')).lower() or 'offshore' in p.get('brand', '').lower() or 'monero' in str(p.get('tags', '')).lower())
    cnt_10g = sum(1 for p in providers if '10g' in str(p.get('tags', '')).lower() or '10gbps' in str(p.get('port_speed', '')).lower())
    cnt_dedicated = sum(1 for p in providers if 'dedicated' in str(p.get('server_type', '')).lower() or 'bare metal' in str(p.get('server_type', '')).lower())

    # Region counts
    reg_counter = Counter(p.get('region', 'Europe').lower() for p in providers)
    cnt_reg_all = total_count
    cnt_reg_eu = reg_counter.get('europe', 0)
    cnt_reg_na = reg_counter.get('north america', 0)
    cnt_reg_ap = reg_counter.get('asia-pacific', 0)
    cnt_reg_me = reg_counter.get('middle east', 0)
    cnt_reg_la = reg_counter.get('south america', 0) + reg_counter.get('latin america', 0)
    cnt_reg_af = reg_counter.get('africa', 0)

    # Country counts
    country_counter = Counter(p.get('country') for p in providers if p.get('country'))
    sorted_countries = country_counter.most_common()

    # Latency Tiers for Spectrum Bar
    tier_counts = [
        cnt_sub50,
        cnt_lowlat,
        cnt_stdeu,
        sum(1 for p in providers if 120 <= float(p.get('avg_ms') or 9999) < 200),
        sum(1 for p in providers if float(p.get('avg_ms') or 9999) >= 200 and float(p.get('avg_ms') or 9999) < 9000)
    ]
    tot_tiers = max(1, sum(tier_counts))
    tier_pcts = [max(1.5, round((c / tot_tiers) * 100, 1)) if c > 0 else 0 for c in tier_counts]

    # Best Spotlights
    best_overall = min(providers, key=lambda x: float(x.get('avg_ms') or 9999))
    bo_iso_l, bo_iso_u = get_iso(best_overall.get('country'), best_overall.get('country_code'))

    eu_providers = [p for p in providers if p.get('region') == 'Europe' and p.get('avg_ms')]
    best_eu = min(eu_providers, key=lambda x: float(x.get('avg_ms') or 9999)) if eu_providers else best_overall
    be_iso_l, be_iso_u = get_iso(best_eu.get('country'), best_eu.get('country_code'))

    hr_providers = [p for p in providers if (p.get('hourly_billing') or 'hour' in str(p.get('billing_model', '')).lower()) and p.get('avg_ms')]
    best_hr = min(hr_providers, key=lambda x: float(x.get('avg_ms') or 9999)) if hr_providers else best_overall
    bh_iso_l, bh_iso_u = get_iso(best_hr.get('country'), best_hr.get('country_code'))

    cr_providers = [p for p in providers if p.get('crypto') and p.get('avg_ms')]
    best_cr = min(cr_providers, key=lambda x: float(x.get('avg_ms') or 9999)) if cr_providers else best_overall
    bc_iso_l, bc_iso_u = get_iso(best_cr.get('country'), best_cr.get('country_code'))

    # 3. Build Sidebar HTML
    country_items_html = [
        f'<button type="button" class="sb-country-item active" data-country-val="all" onclick="setCountry(\'all\')">'
        f'<div class="sb-c-left"><span class="sb-iso-all">ALL</span><span>All Countries</span></div>'
        f'<span class="sb-count">{total_count}</span></button>'
    ]
    for c_name, c_cnt in sorted_countries:
        c_iso_l, c_iso_u = get_iso(c_name)
        c_val = c_name.lower()
        country_items_html.append(
            f'<button type="button" class="sb-country-item" data-country-val="{c_val}" data-country-name="{c_val} {c_iso_l}" onclick="setCountry(\'{c_val}\')">\n'
            f'      <div class="sb-c-left">\n'
            f'        <img class="flag-icon" src="https://flagcdn.com/w40/{c_iso_l}.png" alt="{c_iso_u}" loading="lazy" onerror="this.style.display=\'none\'" decoding="async">\n'
            f'        <span class="sb-c-name">{c_name}</span>\n'
            f'        <span class="sb-c-iso">{c_iso_u}</span>\n'
            f'      </div>\n'
            f'      <span class="sb-count">{c_cnt}</span>\n'
            f'    </button>'
        )

    sidebar_html = f"""<aside class="app-sidebar" id="appSidebar">
    <div class="sb-mobile-header">
      <div class="sb-mobile-title">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 3.5h12M4.5 8h7M6.5 12.5h3" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
        <span>Filter &amp; Country Directory</span>
      </div>
      <button type="button" class="sb-close-btn" onclick="closeMobileSidebar()">Done ✕</button>
    </div>

    <div class="sb-section">
      <div class="sb-title">
        <span>CATEGORIES &amp; PRESETS</span>
        <button type="button" class="sb-reset-btn" onclick="resetAllFilters()">Reset All</button>
      </div>
      <div class="sb-nav-list">
        <button type="button" class="sb-item active" data-cat="all" onclick="setCategory('all')">
          <span class="sb-item-left"><span class="sb-dot" style="background:var(--cyan-bright);"></span>All Verified Clouds</span>
          <span class="sb-count">{cnt_all}</span>
        </button>
        <button type="button" class="sb-item" data-cat="sub_50" onclick="setCategory('sub_50')">
          <span class="sb-item-left"><span class="sb-dot" style="background:var(--emerald-bright);"></span>Sub-50ms Direct (Iran)</span>
          <span class="sb-count">{cnt_sub50}</span>
        </button>
        <button type="button" class="sb-item" data-cat="low_latency" onclick="setCategory('low_latency')">
          <span class="sb-item-left"><span class="sb-dot" style="background:var(--teal-bright);"></span>50–80ms Prime Europe</span>
          <span class="sb-count">{cnt_lowlat}</span>
        </button>
        <button type="button" class="sb-item" data-cat="std_eu" onclick="setCategory('std_eu')">
          <span class="sb-item-left"><span class="sb-dot" style="background:var(--cyan-bright);"></span>80–120ms West Europe</span>
          <span class="sb-count">{cnt_stdeu}</span>
        </button>
        <button type="button" class="sb-item" data-cat="hourly" onclick="setCategory('hourly')">
          <span class="sb-item-left"><span class="sb-dot" style="background:#38bdf8;"></span>Hourly Pay-As-You-Go</span>
          <span class="sb-count">{cnt_hourly}</span>
        </button>
        <button type="button" class="sb-item" data-cat="crypto" onclick="setCategory('crypto')">
          <span class="sb-item-left"><span class="sb-dot" style="background:var(--amber-bright);"></span>Crypto Accepted</span>
          <span class="sb-count">{cnt_crypto}</span>
        </button>
        <button type="button" class="sb-item" data-cat="budget" onclick="setCategory('budget')">
          <span class="sb-item-left"><span class="sb-dot" style="background:#2dd4bf;"></span>Budget Friendly (&lt;$4/mo)</span>
          <span class="sb-count">{cnt_budget}</span>
        </button>
        <button type="button" class="sb-item" data-cat="ddos" onclick="setCategory('ddos')">
          <span class="sb-item-left"><span class="sb-dot" style="background:#f59e0b;"></span>DDoS Protected</span>
          <span class="sb-count">{cnt_ddos}</span>
        </button>
        <button type="button" class="sb-item" data-cat="privacy" onclick="setCategory('privacy')">
          <span class="sb-item-left"><span class="sb-dot" style="background:#c084fc;"></span>Privacy &amp; Offshore</span>
          <span class="sb-count">{cnt_privacy}</span>
        </button>
        <button type="button" class="sb-item" data-cat="10g" onclick="setCategory('10g')">
          <span class="sb-item-left"><span class="sb-dot" style="background:#60a5fa;"></span>10Gbps+ Uplink</span>
          <span class="sb-count">{cnt_10g}</span>
        </button>
        <button type="button" class="sb-item" data-cat="dedicated" onclick="setCategory('dedicated')">
          <span class="sb-item-left"><span class="sb-dot" style="background:#94a3b8;"></span>Dedicated / Bare Metal</span>
          <span class="sb-count">{cnt_dedicated}</span>
        </button>
      </div>
    </div>

    <div class="sb-section">
      <div class="sb-title"><span>CONTINENT / REGION</span></div>
      <div class="sb-region-grid">
        <button type="button" class="sb-reg-btn full-span active" data-reg="all" onclick="setRegion('all')">
          <span>All Continents</span><small>{cnt_reg_all}</small>
        </button>
        <button type="button" class="sb-reg-btn" data-reg="europe" onclick="setRegion('europe')">
          <span>Europe</span><small>{cnt_reg_eu}</small>
        </button>
        <button type="button" class="sb-reg-btn" data-reg="north america" onclick="setRegion('north america')">
          <span>N. America</span><small>{cnt_reg_na}</small>
        </button>
        <button type="button" class="sb-reg-btn" data-reg="asia-pacific" onclick="setRegion('asia-pacific')">
          <span>Asia-Pacific</span><small>{cnt_reg_ap}</small>
        </button>
        <button type="button" class="sb-reg-btn" data-reg="middle east" onclick="setRegion('middle east')">
          <span>Middle East</span><small>{cnt_reg_me}</small>
        </button>
        <button type="button" class="sb-reg-btn" data-reg="latin america" onclick="setRegion('latin america')">
          <span>Latin America</span><small>{cnt_reg_la}</small>
        </button>
        <button type="button" class="sb-reg-btn" data-reg="africa" onclick="setRegion('africa')">
          <span>Africa</span><small>{cnt_reg_af}</small>
        </button>
      </div>
    </div>

    <div class="sb-section">
      <div class="sb-title"><span>COUNTRY DIRECTORY ({unique_countries_count})</span></div>
      <input type="text" id="countryQuickSearch" class="sb-country-search" placeholder="Search country or ISO code..." oninput="filterCountryList(this.value)">
      <div class="sb-country-list" id="sidebarCountryList">
        {chr(10).join(country_items_html)}
      </div>
    </div>

    <div class="sb-section">
      <div class="sb-title"><span>TECHNICAL PARAMETERS</span></div>
      <div class="sb-select-group">
        <div class="sb-field">
          <label for="latencyFilter">Iran Latency Threshold</label>
          <select id="latencyFilter" class="sb-select" onchange="applyFiltersAndSort()">
            <option value="all">All Latency Bands</option>
            <option value="under_50">Sub-50ms (Regional Direct)</option>
            <option value="50_80">50ms – 80ms (Prime Europe)</option>
            <option value="80_120">80ms – 120ms (West Europe)</option>
            <option value="120_200">120ms – 200ms (US East / Asia)</option>
            <option value="over_200">200ms+ (US West / Oceania)</option>
          </select>
        </div>

        <div class="sb-field">
          <label for="priceFilter">Monthly Price Bracket</label>
          <select id="priceFilter" class="sb-select" onchange="applyFiltersAndSort()">
            <option value="all">All Price Tiers</option>
            <option value="under_3">Budget: Under $3.00/mo</option>
            <option value="3_6">Standard: $3.00 – $6.00/mo</option>
            <option value="6_15">Mid-Range: $6.00 – $15.00/mo</option>
            <option value="over_15">Enterprise: Over $15.00/mo</option>
          </select>
        </div>

        <div class="sb-field">
          <label for="portFilter">Port Speed / Uplink</label>
          <select id="portFilter" class="sb-select" onchange="applyFiltersAndSort()">
            <option value="all">All Uplink Speeds</option>
            <option value="10g">10 Gbps+ High-Speed</option>
            <option value="1g">1 Gbps Standard</option>
          </select>
        </div>
      </div>
    </div>
  </aside>"""

    # 4. Build Hero Spotlight Cards & Main Stage Top
    bo_ms = float(best_overall.get('avg_ms') or 0.0)
    be_ms = float(best_eu.get('avg_ms') or 0.0)
    bh_ms = float(best_hr.get('avg_ms') or 0.0)
    bc_ms = float(best_cr.get('avg_ms') or 0.0)

    main_stage_top = f"""  <main class="app-main">

    <section class="spotlight-grid">
      <div class="spot-card" data-kpi-cat="sub_50" onclick="setCategory('sub_50')">
        <div class="spot-top">
          <span class="spot-label">Lowest Latency to Iran</span>
          <span class="spot-pill" style="background:var(--emerald-bg); color:var(--emerald-bright);">Direct Fiber</span>
        </div>
        <div class="spot-metric">
          <span class="spot-val" style="color:var(--emerald-bright);">{bo_ms:.2f}</span>
          <span class="spot-unit">ms</span>
        </div>
        <div class="spot-footer">
          <img class="flag-icon" src="https://flagcdn.com/w40/{bo_iso_l}.png" alt="{bo_iso_u}" decoding="async">
          <span>{best_overall.get('brand')} · {best_overall.get('city') or best_overall.get('country')}, {best_overall.get('country')}</span>
        </div>
      </div>

      <div class="spot-card" data-kpi-cat="low_latency" onclick="setCategory('low_latency')">
        <div class="spot-top">
          <span class="spot-label">Fastest Europe Cloud</span>
          <span class="spot-pill" style="background:var(--teal-bg); color:var(--teal-bright);">Frankfurt IX</span>
        </div>
        <div class="spot-metric">
          <span class="spot-val" style="color:var(--teal-bright);">{be_ms:.2f}</span>
          <span class="spot-unit">ms</span>
        </div>
        <div class="spot-footer">
          <img class="flag-icon" src="https://flagcdn.com/w40/{be_iso_l}.png" alt="{be_iso_u}" decoding="async">
          <span>{best_eu.get('brand')} · {best_eu.get('city') or best_eu.get('country')}, {best_eu.get('country')}</span>
        </div>
      </div>

      <div class="spot-card" data-kpi-cat="hourly" onclick="setCategory('hourly')">
        <div class="spot-top">
          <span class="spot-label">Fastest Hourly Cloud</span>
          <span class="spot-pill" style="background:var(--cyan-bg); color:var(--cyan-bright);">Pay-As-You-Go</span>
        </div>
        <div class="spot-metric">
          <span class="spot-val" style="color:var(--cyan-bright);">{bh_ms:.2f}</span>
          <span class="spot-unit">ms</span>
        </div>
        <div class="spot-footer">
          <img class="flag-icon" src="https://flagcdn.com/w40/{bh_iso_l}.png" alt="{bh_iso_u}" decoding="async">
          <span>{best_hr.get('brand')} · {best_hr.get('city') or best_hr.get('country')} ({best_hr.get('starting_price')})</span>
        </div>
      </div>

      <div class="spot-card" data-kpi-cat="crypto" onclick="setCategory('crypto')">
        <div class="spot-top">
          <span class="spot-label">Fastest Crypto Cloud</span>
          <span class="spot-pill" style="background:var(--amber-bg); color:var(--amber-bright);">BTC · USDT</span>
        </div>
        <div class="spot-metric">
          <span class="spot-val" style="color:var(--amber-bright);">{bc_ms:.2f}</span>
          <span class="spot-unit">ms</span>
        </div>
        <div class="spot-footer">
          <img class="flag-icon" src="https://flagcdn.com/w40/{bc_iso_l}.png" alt="{bc_iso_u}" decoding="async">
          <span>{best_cr.get('brand')} · {cnt_crypto} Crypto Hosts</span>
        </div>
      </div>
    </section>

    <section class="spectrum-card">
      <div class="spectrum-top">
        <div class="spectrum-title">
          <span>LIVE IRAN LATENCY DISTRIBUTION</span>
          <span style="color:var(--text-muted); font-weight:500;">(Click any tier to filter)</span>
        </div>
        <div class="spectrum-legend">
          <span class="legend-pill" onclick="setLatencySelect('under_50')"><span class="legend-dot" style="background:var(--emerald-bright);"></span>&lt;50ms: <strong id="specCnt1">{tier_counts[0]}</strong></span>
          <span class="legend-pill" onclick="setLatencySelect('50_80')"><span class="legend-dot" style="background:var(--teal-bright);"></span>50–80ms: <strong id="specCnt2">{tier_counts[1]}</strong></span>
          <span class="legend-pill" onclick="setLatencySelect('80_120')"><span class="legend-dot" style="background:var(--cyan-bright);"></span>80–120ms: <strong id="specCnt3">{tier_counts[2]}</strong></span>
          <span class="legend-pill" onclick="setLatencySelect('120_200')"><span class="legend-dot" style="background:var(--amber-bright);"></span>120–200ms: <strong id="specCnt4">{tier_counts[3]}</strong></span>
          <span class="legend-pill" onclick="setLatencySelect('over_200')"><span class="legend-dot" style="background:var(--rose-bright);"></span>200ms+: <strong id="specCnt5">{tier_counts[4]}</strong></span>
        </div>
      </div>
      <div class="spectrum-bar">
        <div class="spec-seg" id="specSeg1" style="width:{tier_pcts[0]}%; background:var(--emerald-bright);" onclick="setLatencySelect('under_50')"></div>
        <div class="spec-seg" id="specSeg2" style="width:{tier_pcts[1]}%; background:var(--teal-bright);" onclick="setLatencySelect('50_80')"></div>
        <div class="spec-seg" id="specSeg3" style="width:{tier_pcts[2]}%; background:var(--cyan-bright);" onclick="setLatencySelect('80_120')"></div>
        <div class="spec-seg" id="specSeg4" style="width:{tier_pcts[3]}%; background:var(--amber-bright);" onclick="setLatencySelect('120_200')"></div>
        <div class="spec-seg" id="specSeg5" style="width:{tier_pcts[4]}%; background:var(--rose-bright);" onclick="setLatencySelect('over_200')"></div>
      </div>
    </section>

    <section class="workspace-toolbar">
      <div class="toolbar-main">
        <div class="search-wrap">
          <svg class="search-ico" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.7"/>
            <path d="M11 11L14.2 14.2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
          </svg>
          <input type="text" id="searchInput" class="main-search" placeholder="Search provider brand, ASN (e.g. AS63949), city, test IPv4, or hardware..." />
          <span class="kbd-hint" id="searchKbd">Press /</span>
          <button type="button" id="clearSearch" class="clear-search-btn" onclick="clearSearchInput()">Clear ✕</button>
        </div>

        <div class="toolbar-right">
          <div class="telemetry-summary">
            <span>Showing <strong id="visibleCount">{total_count}</strong> / {total_count}</span>
            <span>·</span>
            <span>Avg: <strong id="meanPingStat">{avg_ping} ms</strong></span>
            <span>·</span>
            <span>Best: <strong id="minPingStat">{min_ping} ms</strong></span>
          </div>

          <select id="sortSelect" class="sort-select" onchange="handleSortChange()">
            <option value="ping_asc">Sort: Lowest Iran Ping First</option>
            <option value="ping_desc">Sort: Highest Ping First</option>
            <option value="price_asc">Sort: Lowest Price First</option>
            <option value="price_desc">Sort: Highest Price First</option>
            <option value="jitter_asc">Sort: Lowest Jitter (Most Stable)</option>
            <option value="brand_asc">Sort: Provider Name (A → Z)</option>
            <option value="country_asc">Sort: Country Name (A → Z)</option>
          </select>
        </div>
      </div>

      <div class="quick-ribbon" id="quickRibbon">
        <button type="button" class="qr-pill active" data-cat="all" onclick="setCategory('all')">All ({cnt_all})</button>
        <button type="button" class="qr-pill" data-cat="sub_50" onclick="setCategory('sub_50')">&lt;50ms Iran ({cnt_sub50})</button>
        <button type="button" class="qr-pill" data-cat="low_latency" onclick="setCategory('low_latency')">50–80ms EU ({cnt_lowlat})</button>
        <button type="button" class="qr-pill" data-cat="std_eu" onclick="setCategory('std_eu')">80–120ms EU ({cnt_stdeu})</button>
        <button type="button" class="qr-pill" data-cat="hourly" onclick="setCategory('hourly')">Hourly ({cnt_hourly})</button>
        <button type="button" class="qr-pill" data-cat="crypto" onclick="setCategory('crypto')">Crypto ({cnt_crypto})</button>
        <button type="button" class="qr-pill" data-cat="budget" onclick="setCategory('budget')">Budget &lt;$4 ({cnt_budget})</button>
        <button type="button" class="qr-pill" data-cat="ddos" onclick="setCategory('ddos')">DDoS ({cnt_ddos})</button>
        <button type="button" class="qr-pill" data-cat="privacy" onclick="setCategory('privacy')">Privacy ({cnt_privacy})</button>
        <button type="button" class="qr-pill" data-cat="10g" onclick="setCategory('10g')">10Gbps+ ({cnt_10g})</button>
      </div>

      <div class="active-filters-bar" id="activeFiltersBar">
        <div class="active-tags-list" id="activeFilterTags"></div>
        <button type="button" class="sb-reset-btn" onclick="resetAllFilters()">Clear All Active Filters</button>
      </div>
    </section>

    <div class="table-container">
      <div class="table-scroll">
        <table id="resultsTable">
          <thead>
            <tr>
              <th style="width:72px;">#</th>
              <th class="sortable" id="th_brand" onclick="sortTableColumn('brand')">Provider &amp; ASN <span class="sort-arrow" id="arrow_brand">↕</span></th>
              <th class="sortable" id="th_country" onclick="sortTableColumn('country')">Location <span class="sort-arrow" id="arrow_country">↕</span></th>
              <th class="sortable sorted-active" id="th_ping" onclick="sortTableColumn('ping')">Iran Latency (Respina) <span class="sort-arrow" id="arrow_ping">↑</span></th>
              <th class="sortable" id="th_price" onclick="sortTableColumn('price')">Pricing &amp; Billing <span class="sort-arrow" id="arrow_price">↕</span></th>
              <th>Hardware &amp; Uplink</th>
              <th>Payment</th>
              <th>Test IPv4 &amp; Looking Glass</th>
            </tr>
          </thead>
          <tbody>"""

    # 5. Build Table Rows
    rows_html = []
    for idx, p in enumerate(providers, 1):
        brand = p.get('brand', 'Unknown')
        brand_l = brand.lower()
        website = p.get('website', '')
        asn_str = p.get('verified_asn', '')
        asn_match = re.search(r'(AS\d+)', asn_str)
        asn_only = asn_match.group(1) if asn_match else (asn_str[:10] if asn_str else "N/A")
        
        country = p.get('country', 'Unknown')
        country_l = country.lower()
        iso_l, iso_u = get_iso(country, p.get('country_code'))
        city = p.get('city') or ''
        region = p.get('region', 'Europe')
        region_l = region.lower()

        ping = float(p.get('avg_ms') or 9999.0)
        jitter = float(p.get('jitter_ms') or 0.0)
        min_p = float(p.get('min_ms') or ping)
        max_p = float(p.get('max_ms') or ping)
        loss = float(p.get('loss_pct') or 0.0)

        # Latency Tier
        if ping < 50:
            tier_cls = "tier-1"
            tier_label = "Direct Fiber"
            bar_pct = max(6, int((ping / 50.0) * 20))
        elif ping < 80:
            tier_cls = "tier-2"
            tier_label = "Prime Europe"
            bar_pct = max(20, int((ping / 80.0) * 45))
        elif ping < 120:
            tier_cls = "tier-3"
            tier_label = "West Europe"
            bar_pct = max(45, int((ping / 120.0) * 70))
        elif ping < 200:
            tier_cls = "tier-4"
            tier_label = "US East / Asia"
            bar_pct = max(70, int((ping / 200.0) * 90))
        else:
            tier_cls = "tier-5"
            tier_label = "Global Reach"
            bar_pct = 98

        # Pricing & Billing
        is_hourly = bool(p.get('hourly_billing') or 'hour' in str(p.get('billing_model', '')).lower())
        price_disp = p.get('starting_price', '$4.00/mo')
        num_price = parse_price(price_disp)
        
        # Payment
        is_crypto = bool(p.get('crypto'))
        
        # Tags & Categories
        tags_str = " ".join(p.get('tags', [])).lower()
        is_sub50 = str(ping < 50).lower()
        is_lowlat = str(50 <= ping < 80).lower()
        is_stdeu = str(80 <= ping < 120).lower()
        is_10g = str('10g' in tags_str or '10gbps' in str(p.get('port_speed', '')).lower()).lower()
        is_ddos = str('ddos' in brand_l or 'ddos' in tags_str).lower()
        is_privacy = str('privacy' in tags_str or 'offshore' in brand_l or 'monero' in tags_str).lower()
        is_budget = str(num_price < 4.0).lower()
        is_dedicated = str('dedicated' in str(p.get('server_type', '')).lower() or 'bare metal' in str(p.get('server_type', '')).lower()).lower()

        server_spec = p.get('server_type', 'Cloud VPS & Dedicated Servers')
        port_speed = p.get('port_speed', '1Gbps - 10Gbps')
        uplink_cls = "uplink-10g" if is_10g == 'true' else "uplink-1g"

        if is_crypto:
            pay_html = '<span class="pay-pill pay-crypto">🪙 Crypto</span>'
        else:
            pay_html = '<span class="pay-pill pay-fiat">Card / Fiat</span>'

        test_ip = p.get('test_ip', '')
        lg_url = p.get('looking_glass_url') or website or f"http://{test_ip}"

        row = f"""        <tr data-id="{idx}" data-brand="{brand_l}" data-brand-display="{brand}" data-asn="{asn_only}" data-category="{'hourly' if is_hourly else 'monthly'}" data-crypto="{str(is_crypto).lower()}" data-hourly="{str(is_hourly).lower()}" data-sub50="{is_sub50}" data-lowlat="{is_lowlat}" data-stdeu="{is_stdeu}" data-10g="{is_10g}" data-ddos="{is_ddos}" data-privacy="{is_privacy}" data-budget="{is_budget}" data-dedicated="{is_dedicated}" data-country="{country_l}" data-country-display="{country}" data-iso="{iso_u}" data-iso-lower="{iso_l}" data-city="{city}" data-region="{region_l}" data-ping="{ping:.2f}" data-jitter="{jitter:.1f}" data-min="{min_p:.1f}ms" data-max="{max_p:.1f}ms" data-loss="{loss:.1f}%" data-tier="{tier_cls}" data-tier-label="{tier_label}" data-price="{num_price}" data-price-display="{price_disp}" data-price-main="{price_disp}" data-price-sub="" data-port="{port_speed.lower()}" data-port-display="{port_speed}" data-server="{server_spec}" data-ip="{test_ip}" data-url="{website}" data-lg="{lg_url}">
          <td class="col-rank">
            <div class="rank-cell">
              <button type="button" class="pin-btn" onclick="toggleCompare({idx}, this)" title="Compare Provider">
                <svg width="13" height="13"><use href="#ico-plus"/></svg>
              </button>
              <span class="row-num">{idx}</span>
            </div>
          </td>
          <td class="col-provider">
            <div class="provider-wrap">
              <a href="{website}" target="_blank" rel="noopener" class="provider-name">
                <span>{brand}</span>
                <svg class="ext-ico" width="12" height="12"><use href="#ico-ext"/></svg>
              </a>
              <div class="provider-meta">
                <span class="asn-badge">{asn_only}</span>
              </div>
            </div>
          </td>
          <td class="col-location">
            <div class="loc-wrap">
              <img class="flag-lg" src="https://flagcdn.com/w40/{iso_l}.png" alt="{iso_u}" loading="lazy" onerror="this.style.display='none'">
              <div class="loc-text">
                <div class="loc-country-row">
                  <span class="loc-country-name">{country}</span>
                  <span class="loc-iso-badge">{iso_u}</span>
                </div>
                <span class="loc-city-name">{city}</span>
              </div>
            </div>
          </td>
          <td class="col-ping">
            <div class="ping-box {tier_cls}">
              <div class="ping-top">
                <div class="ping-badge">
                  <span class="ping-dot"></span>
                  <span class="ping-num">{ping:.2f}</span>
                  <span class="ping-ms">ms</span>
                </div>
                <span class="jitter-pill" title="ICMP Jitter">±{jitter:.1f}ms</span>
              </div>
              <div class="ping-bar-bg">
                <div class="ping-bar-fg" style="width:{bar_pct}%;"></div>
              </div>
              <div class="ping-sub-metrics">
                <span>Min {min_p:.1f}ms</span>
                <span>·</span>
                <span>Max {max_p:.1f}ms</span>
                <span>·</span>
                <span>Loss {loss:.1f}%</span>
              </div>
            </div>
          </td>
          <td class="col-pricing">
            <div class="price-wrap">
              <span class="price-main {('is-hourly' if is_hourly else '')}">{price_disp}</span>
              <span class="bill-pill {('bill-hourly' if is_hourly else 'bill-monthly')}">{'⏱️ Hourly' if is_hourly else 'Monthly Billing'}</span>
            </div>
          </td>
          <td class="col-specs">
            <div class="specs-wrap">
              <span class="server-spec">{server_spec}</span>
              <span class="uplink-badge {uplink_cls}">{port_speed}</span>
            </div>
          </td>
          <td class="col-payment">
            {pay_html}
          </td>
          <td class="col-actions">
            <div class="action-group">
              <button type="button" class="ip-copy-pill" onclick="copyIP('{test_ip}', this)" title="Click to Copy Test IPv4">
                <span class="ip-addr">{test_ip}</span>
                <svg width="13" height="13"><use href="#ico-copy"/></svg>
              </button>
              <a class="lg-btn" href="{lg_url}" target="_blank" rel="noopener" title="Open Looking Glass">
                <span>Looking Glass</span>
                <svg width="12" height="12"><use href="#ico-ext"/></svg>
              </a>
            </div>
          </td>
        </tr>"""
        rows_html.append(row)

    # 6. Extract Footer part (from <tr id="noResultsRow" onward)
    no_res_marker = '<tr id="noResultsRow"'
    no_res_idx = template_text.find(no_res_marker)
    if no_res_idx == -1:
        raise ValueError("Could not find <tr id=\"noResultsRow\" in template!")

    footer_part = template_text[no_res_idx:]

    # Assemble Full Document
    full_html = (
        head_part + "\n" +
        sidebar_html + "\n\n" +
        main_stage_top + "\n" +
        "\n".join(rows_html) + "\n        " +
        footer_part
    )

    return full_html
