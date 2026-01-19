#!/usr/bin/env python3
"""Inspect PDF structure to understand format."""

import pdfplumber
from pathlib import Path

pdf_path = Path("/Users/fjabbari/@@@PUBLIC/@@@TAX2025/eStmt_2025-01-24.pdf")

print("Inspecting PDF structure...")
print("=" * 70)

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    for page_num, page in enumerate(pdf.pages[:3], 1):  # First 3 pages
        print(f"\n--- Page {page_num} ---")
        text = page.extract_text()
        
        if text:
            lines = text.split('\n')
            print(f"Total lines: {len(lines)}")
            print("\nFirst 30 lines:")
            for i, line in enumerate(lines[:30], 1):
                if line.strip():
                    print(f"{i:3d}: {line[:80]}")
        
        # Try tables
        tables = page.extract_tables()
        if tables:
            print(f"\nFound {len(tables)} tables on page {page_num}")
            for i, table in enumerate(tables[:2], 1):
                print(f"\nTable {i} (first 5 rows):")
                for row_idx, row in enumerate(table[:5], 1):
                    print(f"  Row {row_idx}: {row}")
