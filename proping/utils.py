# -*- coding: utf-8 -*-
"""
ProPing Utilities
ISO country mapping, price normalizer, and data sanitation routines.
"""

import re

COUNTRY_ISO_MAP = {
    'Albania': 'al', 'Armenia': 'am', 'Australia': 'au', 'Austria': 'at',
    'Bangladesh': 'bd', 'Belarus': 'by', 'Belgium': 'be', 'Belize': 'bz',
    'Bosnia and Herzegovina': 'ba', 'Brazil': 'br', 'Bulgaria': 'bg',
    'Canada': 'ca', 'Chile': 'cl', 'Costa Rica': 'cr', 'Cyprus': 'cy',
    'Czech Republic': 'cz', 'Czechia': 'cz', 'Dominica': 'dm', 'Estonia': 'ee',
    'Finland': 'fi', 'France': 'fr', 'Georgia': 'ge', 'Germany': 'de', 'Greece': 'gr',
    'Hong Kong': 'hk', 'Hungary': 'hu', 'Iceland': 'is', 'India': 'in',
    'Indonesia': 'id', 'Ireland': 'ie', 'Israel': 'il', 'Italy': 'it',
    'Japan': 'jp', 'Kazakhstan': 'kz', 'Kyrgyzstan': 'kg', 'Latvia': 'lv',
    'Lithuania': 'lt', 'Luxembourg': 'lu', 'Malaysia': 'my', 'Mauritius': 'mu',
    'Mexico': 'mx', 'Moldova': 'md', 'Morocco': 'ma', 'Netherlands': 'nl',
    'New Zealand': 'nz', 'Nigeria': 'ng', 'Norway': 'no', 'Panama': 'pa',
    'Poland': 'pl', 'Portugal': 'pt', 'Romania': 'ro', 'Russia': 'ru',
    'Serbia': 'rs', 'Seychelles': 'sc', 'Singapore': 'sg', 'Slovakia': 'sk',
    'South Korea': 'kr', 'Spain': 'es', 'Sweden': 'se', 'Switzerland': 'ch',
    'Taiwan': 'tw', 'Thailand': 'th', 'Turkey': 'tr', 'Ukraine': 'ua',
    'United Arab Emirates': 'ae', 'United Kingdom': 'gb', 'United States': 'us',
    'Vietnam': 'vn',
}

CODE_TO_COUNTRY = {
    'AE': 'United Arab Emirates', 'AL': 'Albania', 'AM': 'Armenia', 'AT': 'Austria',
    'AU': 'Australia', 'BA': 'Bosnia and Herzegovina', 'BD': 'Bangladesh', 'BE': 'Belgium',
    'BG': 'Bulgaria', 'BR': 'Brazil', 'BY': 'Belarus', 'BZ': 'Belize',
    'CA': 'Canada', 'CH': 'Switzerland', 'CL': 'Chile', 'CR': 'Costa Rica',
    'CY': 'Cyprus', 'CZ': 'Czechia', 'DE': 'Germany', 'DM': 'Dominica',
    'EE': 'Estonia', 'ES': 'Spain', 'FI': 'Finland', 'FR': 'France',
    'GB': 'United Kingdom', 'GE': 'Georgia', 'GR': 'Greece', 'HK': 'Hong Kong',
    'HU': 'Hungary', 'ID': 'Indonesia', 'IE': 'Ireland', 'IL': 'Israel',
    'IN': 'India', 'IS': 'Iceland', 'IT': 'Italy', 'JP': 'Japan',
    'KG': 'Kyrgyzstan', 'KR': 'South Korea', 'KZ': 'Kazakhstan', 'LT': 'Lithuania',
    'LU': 'Luxembourg', 'LV': 'Latvia', 'MA': 'Morocco', 'MD': 'Moldova',
    'MX': 'Mexico', 'MY': 'Malaysia', 'NG': 'Nigeria', 'NL': 'Netherlands',
    'NO': 'Norway', 'NZ': 'New Zealand', 'PA': 'Panama', 'PL': 'Poland',
    'PT': 'Portugal', 'RO': 'Romania', 'RS': 'Serbia', 'RU': 'Russia',
    'SC': 'Seychelles', 'SE': 'Sweden', 'SG': 'Singapore', 'SK': 'Slovakia',
    'TH': 'Thailand', 'TR': 'Turkey', 'TW': 'Taiwan', 'UA': 'Ukraine',
    'US': 'United States', 'VN': 'Vietnam'
}

BRAND_SANITIZATIONS = {
    '★ Dyjix SAS': 'Dyjix SAS',
    'UP-NETWORK Sàrl': 'UP-NETWORK Sarl',
    'Kättare': 'Kattare'
}

def get_iso(country_name, code=None):
    """Return (iso_lower, iso_upper) for a country name or code."""
    if code and len(code) == 2:
        return code.lower(), code.upper()
    iso = COUNTRY_ISO_MAP.get(country_name, 'un').lower()
    return iso, iso.upper()

def parse_price(p):
    """Normalize starting price string to monthly USD equivalent float."""
    p_str = str(p or '').lower()
    if '₺99' in p_str:
        return 2.90
    if 'rp 50k' in p_str:
        return 3.20
    if 'r$ 29' in p_str:
        return 5.50
    if '/yr' in p_str:
        m = re.search(r'[\$€£₺]?\s*([0-9.]+)', p_str)
        if m:
            return round(float(m.group(1)) / 12.0, 2)
    m = re.search(r'[\$€£₺]?\s*([0-9.]+)', p_str)
    if m:
        try:
            return float(m.group(1))
        except:
            return 999.0
    return 999.0

def clean_record(p):
    """Sanitize provider metadata for clean catalog presentation."""
    brand = p.get('brand', '')
    if brand in BRAND_SANITIZATIONS:
        p['brand'] = BRAND_SANITIZATIONS[brand]
    elif brand.startswith('★ '):
        p['brand'] = brand.replace('★ ', '').strip()

    country = p.get('country', '').strip()
    if len(country) == 2 and country.upper() in CODE_TO_COUNTRY:
        code = country.upper()
        p['country'] = CODE_TO_COUNTRY[code]
        p['country_code'] = code
    elif country == 'Czech Republic':
        p['country'] = 'Czechia'
        p['country_code'] = 'CZ'
    elif country in COUNTRY_ISO_MAP:
        p['country_code'] = COUNTRY_ISO_MAP[country].upper()

    # Region normalization
    c_name = p.get('country', '')
    if c_name in ['Turkey', 'United Arab Emirates', 'Israel', 'Georgia']:
        p['region'] = 'Middle East'
    elif c_name in ['United States', 'Canada', 'Mexico']:
        p['region'] = 'North America'
    elif c_name in ['Brazil', 'Chile', 'Belize', 'Costa Rica', 'Dominica', 'Panama']:
        p['region'] = 'Latin America'
    elif c_name in ['Australia', 'New Zealand', 'Japan', 'South Korea', 'Singapore', 'Hong Kong', 'Taiwan', 'Malaysia', 'Indonesia', 'Thailand', 'Vietnam', 'India', 'Bangladesh', 'Kazakhstan', 'Kyrgyzstan']:
        p['region'] = 'Asia-Pacific'
    elif c_name in ['Morocco', 'Nigeria', 'Seychelles']:
        p['region'] = 'Africa'
    elif not p.get('region') or p.get('region') == 'Global':
        p['region'] = 'Europe'

    return p
