#!/usr/bin/env python3
"""
Qobrix CRM API client for property management.

Reads credentials from the plugin's standard location:
  $CLAUDE_DIR/plugins/data/real-estate-broker/credentials.json

CLAUDE_DIR is resolved the same way as scripts/qobrix-api.sh:
  1. CLAUDE_PLUGIN_OPTION_QOBRIX_* env vars (override)
  2. Cowork persistent mount /sessions/*/mnt/.claude
  3. $HOME/.claude

Usage:
    python3 qobrix_api.py search-project "<name>" [--developer "<dev-name>"]
    python3 qobrix_api.py list-units "<project-uuid>"
    python3 qobrix_api.py update-property "<property-uuid>" \
        --status "<status>" --price "<price>" --inspection-date "<YYYY-MM-DD>"
    python3 qobrix_api.py get-property "<property-uuid>"
"""

import sys
import json
import os
import glob
import time
import argparse
import subprocess


def install_requests():
    try:
        import requests
        return requests
    except ImportError:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "requests",
            "--break-system-packages", "-q"
        ])
        import requests
        return requests


def resolve_claude_dir():
    """Mirror the bash wrapper's CLAUDE_DIR resolution."""
    if os.path.isdir('/sessions'):
        for d in sorted(glob.glob('/sessions/*/mnt/.claude')):
            if os.path.isdir(d):
                return d
    return os.path.join(os.path.expanduser('~'), '.claude')


def load_config():
    """Load Qobrix API config from env vars then plugin credentials.json."""
    api_url = os.environ.get('CLAUDE_PLUGIN_OPTION_QOBRIX_API_URL') or os.environ.get('QOBRIX_API_URL')
    api_key = os.environ.get('CLAUDE_PLUGIN_OPTION_QOBRIX_API_KEY') or os.environ.get('QOBRIX_API_KEY')
    api_user = os.environ.get('CLAUDE_PLUGIN_OPTION_QOBRIX_API_USER') or os.environ.get('QOBRIX_API_USER')

    creds_path = os.path.join(
        resolve_claude_dir(),
        'plugins', 'data', 'real-estate-broker', 'credentials.json'
    )
    if os.path.exists(creds_path):
        try:
            with open(creds_path) as f:
                creds = json.load(f)
            api_url = api_url or creds.get('qobrix_api_url')
            api_key = api_key or creds.get('qobrix_api_key')
            api_user = api_user or creds.get('qobrix_api_user')
        except Exception:
            pass

    if not (api_url and api_key and api_user):
        return None

    return {
        'api_url': api_url.rstrip('/'),
        'api_key': api_key,
        'api_user': api_user,
    }


def not_configured():
    print(json.dumps({
        'error': 'not_configured',
        'message': 'Qobrix credentials not set. Run /setup to configure them.'
    }))
    sys.exit(1)


class QobrixAPI:
    def __init__(self, config):
        self.requests = install_requests()
        self.base_url = config['api_url']
        self.headers = {
            'X-Api-Key': config['api_key'],
            'X-Api-User': config['api_user'],
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def _request(self, method, endpoint, params=None, data=None, retries=3):
        url = f"{self.base_url}/api/v2/{endpoint.lstrip('/')}"

        for attempt in range(retries):
            try:
                response = self.requests.request(
                    method, url, headers=self.headers,
                    params=params, json=data, timeout=30
                )

                if response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue

                if response.status_code >= 400:
                    return {
                        'error': True,
                        'status_code': response.status_code,
                        'message': response.text,
                    }

                return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {'error': True, 'message': str(e)}

        return {'error': True, 'message': 'Max retries exceeded'}

    def search_projects(self, name, developer_name=None):
        search_expr = f'name contains "{name}"'
        if developer_name:
            search_expr += f' or description contains "{developer_name}"'

        params = {
            'search': search_expr,
            'limit': 20,
            'expand': 'false',
            'fields[]': ['id', 'name', 'description', 'availability_status', 'developer_id'],
        }
        return self._request('GET', 'projects/', params=params)

    def list_project_units(self, project_uuid):
        all_units = []
        page = 1
        while True:
            params = {
                'search': f'project == "{project_uuid}"',
                'limit': 100,
                'page': page,
                'expand': 'false',
                'fields[]': [
                    'id', 'name', 'unit_number', 'status',
                    'list_selling_price_amount', 'inspection_date',
                    'property_type', 'property_subtype',
                    'internal_area_amount', 'total_area_amount',
                    'covered_verandas_amount', 'uncovered_verandas_amount',
                    'bedrooms', 'bathrooms', 'project', 'ref'
                ],
            }
            result = self._request('GET', 'properties/', params=params)
            if 'error' in result and result.get('error'):
                return result
            data = result.get('data', [])
            all_units.extend(data)

            pagination = result.get('pagination', {}) or {}
            if not pagination.get('has_next_page', False):
                break
            page += 1

        return {'data': all_units, 'count': len(all_units)}

    def update_property(self, property_uuid, updates):
        # Qobrix uses PATCH (NOT PUT) for partial updates.
        return self._request('PATCH', f'properties/{property_uuid}', data=updates)

    def get_property(self, property_uuid):
        return self._request('GET', f'properties/{property_uuid}')


def cmd_search_project(args):
    config = load_config()
    if not config:
        not_configured()
    api = QobrixAPI(config)
    print(json.dumps(api.search_projects(args.name, args.developer), indent=2, ensure_ascii=False))


def cmd_list_units(args):
    config = load_config()
    if not config:
        not_configured()
    api = QobrixAPI(config)
    print(json.dumps(api.list_project_units(args.project_uuid), indent=2, ensure_ascii=False))


def cmd_update_property(args):
    config = load_config()
    if not config:
        not_configured()
    api = QobrixAPI(config)

    updates = {}
    if args.status:
        updates['status'] = args.status
    if args.price:
        updates['list_selling_price_amount'] = float(args.price)
    if args.inspection_date:
        # Datetime fields in Qobrix require full ISO with offset; the trailing
        # 'Z' suffix is silently dropped, so we explicitly use +00:00.
        updates['inspection_date'] = f"{args.inspection_date}T00:00:00+00:00"

    print(json.dumps(api.update_property(args.property_uuid, updates), indent=2, ensure_ascii=False))


def cmd_get_property(args):
    config = load_config()
    if not config:
        not_configured()
    api = QobrixAPI(config)
    print(json.dumps(api.get_property(args.property_uuid), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Qobrix CRM API client')
    subparsers = parser.add_subparsers(dest='command')

    sp = subparsers.add_parser('search-project')
    sp.add_argument('name')
    sp.add_argument('--developer')
    sp.set_defaults(func=cmd_search_project)

    lu = subparsers.add_parser('list-units')
    lu.add_argument('project_uuid')
    lu.set_defaults(func=cmd_list_units)

    up = subparsers.add_parser('update-property')
    up.add_argument('property_uuid')
    up.add_argument('--status')
    up.add_argument('--price')
    up.add_argument('--inspection-date')
    up.set_defaults(func=cmd_update_property)

    gp = subparsers.add_parser('get-property')
    gp.add_argument('property_uuid')
    gp.set_defaults(func=cmd_get_property)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)
