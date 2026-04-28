#!/usr/bin/env python3
"""
Parse a developer PDF price list and extract project name, date, and unit data.
Outputs JSON to stdout.

Usage:
    python3 parse_pdf.py <path-to-pdf>
"""

import sys
import json
import re
import subprocess

def install_pdfplumber():
    """Install pdfplumber if not available."""
    try:
        import pdfplumber
        return pdfplumber
    except ImportError:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "pdfplumber",
            "--break-system-packages", "-q"
        ])
        import pdfplumber
        return pdfplumber


def parse_price(price_str):
    """Parse a price string like '423,800' or '430800' into a float."""
    if not price_str or price_str.strip() in ('', '/', '-', 'N/A', 'n/a'):
        return None
    cleaned = re.sub(r'[€$£\s]', '', price_str.strip())
    cleaned = cleaned.replace(',', '')
    try:
        return float(cleaned)
    except ValueError:
        return None


def map_status(pdf_status):
    """Map PDF status text to Qobrix status code."""
    if not pdf_status:
        return None
    status_upper = pdf_status.strip().upper()
    mapping = {
        'SOLD': 'sold',
        'RESERVED': 'reserved',
        'FOR SALE': 'available',
        'FORSALE': 'available',
        'FOR_SALE': 'available',
        'AVAILABLE': 'available',
        'UNDER OFFER': 'under_offer',
        'UNDER_OFFER': 'under_offer',
        'RENTED': 'rented',
        'PENDING': 'pending',
        'WITHDRAWN': 'withdrawn',
    }
    return mapping.get(status_upper, pdf_status.lower().replace(' ', '_'))


def extract_project_name(text_lines):
    """Extract project name from the first lines of the PDF."""
    for line in text_lines[:10]:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^\d{4}\s*[-/]\s*\d{2}\s*[-/]\s*\d{2}$', line):
            continue
        if line.lower() in ('price list', 'pricelist', 'no.', 'house'):
            continue
        if len(line) >= 3 and not line.startswith('Note:'):
            return line
    return None


def extract_date(text_lines):
    """Extract date from PDF text."""
    for line in text_lines[:10]:
        match = re.search(r'(\d{4})\s*[-/]\s*(\d{2})\s*[-/]\s*(\d{2})', line)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        match = re.search(r'(\d{2})\s*[-/]\s*(\d{2})\s*[-/]\s*(\d{4})', line)
        if match:
            return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    return None


def find_table_columns(header_row):
    """Identify column indices from a table header row."""
    if not header_row:
        return {}

    col_map = {}
    for i, cell in enumerate(header_row):
        if not cell:
            continue
        cell_lower = cell.strip().lower()

        if cell_lower in ('no.', 'no', '#', 'unit', 'unit no', 'unit no.'):
            col_map['unit_number'] = i
        elif 'house' in cell_lower and 'type' in cell_lower:
            col_map['type'] = i
        elif cell_lower in ('type',):
            col_map['type'] = i
        elif 'price' in cell_lower:
            col_map['price'] = i
        elif cell_lower == 'status':
            col_map['status'] = i
        elif 'apartment' in cell_lower and 'area' in cell_lower and 'total' not in cell_lower:
            col_map['area'] = i
        elif 'total' in cell_lower and 'area' in cell_lower:
            col_map['total_area'] = i
        elif 'covered' in cell_lower and 'veranda' in cell_lower:
            col_map['covered_verandas'] = i
        elif 'uncovered' in cell_lower and 'veranda' in cell_lower:
            col_map['uncovered_verandas'] = i
        elif 'storage' in cell_lower:
            col_map['storage'] = i

    return col_map


def parse_pdf(pdf_path):
    """Main PDF parsing function."""
    pdfplumber = install_pdfplumber()

    result = {
        'project_name': None,
        'date': None,
        'units': []
    }

    with pdfplumber.open(pdf_path) as pdf:
        all_text_lines = []
        all_tables = []

        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text_lines.extend(text.split('\n'))

            tables = page.extract_tables()
            if tables:
                all_tables.extend(tables)

        result['project_name'] = extract_project_name(all_text_lines)
        result['date'] = extract_date(all_text_lines)

        for table in all_tables:
            if not table or len(table) < 2:
                continue

            col_map = {}
            header_idx = 0

            for i, row in enumerate(table):
                candidate_map = find_table_columns(row)
                if 'unit_number' in candidate_map or 'status' in candidate_map:
                    col_map = candidate_map
                    header_idx = i
                    break

            if not col_map:
                col_map = find_table_columns(table[0])
                if not col_map:
                    continue

            for row in table[header_idx + 1:]:
                if not row:
                    continue

                first_cell = str(row[0] or '').strip()
                if not first_cell or first_cell.lower().startswith('note'):
                    continue

                if re.match(r'^m[²2]?$', first_cell):
                    continue

                unit = {}

                if 'unit_number' in col_map:
                    val = row[col_map['unit_number']]
                    unit['unit_number'] = str(val).strip() if val else None

                if 'type' in col_map:
                    val = row[col_map['type']]
                    unit['type'] = str(val).strip() if val else None

                if 'area' in col_map:
                    val = row[col_map['area']]
                    try:
                        unit['area'] = float(str(val).strip()) if val else None
                    except (ValueError, TypeError):
                        unit['area'] = None

                if 'price' in col_map:
                    val = row[col_map['price']]
                    unit['price'] = parse_price(str(val)) if val else None

                if 'status' in col_map:
                    val = row[col_map['status']]
                    raw_status = str(val).strip() if val else None
                    unit['status_raw'] = raw_status
                    unit['status'] = map_status(raw_status)

                if unit.get('unit_number') and unit['unit_number'] not in ('None', ''):
                    result['units'].append(unit)

    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: parse_pdf.py <path-to-pdf>'}))
        sys.exit(1)

    try:
        data = parse_pdf(sys.argv[1])
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)
