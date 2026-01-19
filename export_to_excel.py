#!/usr/bin/env python3
"""
Export SQLite tables to Excel files.
"""

import sqlite3
import pandas as pd
from pathlib import Path

def export_tables_to_excel():
    """Export all SQLite tables to Excel files."""
    
    db_path = "tax_data_2025.db"
    output_dir = Path("/Users/fjabbari/@@@PUBLIC/@@@TAX2025/")
    
    print("=" * 70)
    print("EXPORTING SQLITE TABLES TO EXCEL")
    print("=" * 70)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    # List of tables to export
    tables = [
        'TaxYearSummary',
        'TaxYearDetail',
        'EntitySummary',
        'EntityDetail'
    ]
    
    print(f"\nExporting {len(tables)} tables to: {output_dir}")
    
    for table_name in tables:
        try:
            # Read table into pandas DataFrame
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            
            # Create Excel filename
            excel_filename = output_dir / f"{table_name}.xlsx"
            
            # Export to Excel
            df.to_excel(excel_filename, index=False, engine='openpyxl')
            
            print(f"✓ Exported {table_name}: {len(df)} rows -> {excel_filename}")
            
        except Exception as e:
            print(f"✗ Error exporting {table_name}: {e}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("EXPORT COMPLETE!")
    print("=" * 70)
    print(f"\nExcel files saved to: {output_dir}")
    print("\nFiles created:")
    for table_name in tables:
        excel_file = output_dir / f"{table_name}.xlsx"
        if excel_file.exists():
            file_size = excel_file.stat().st_size / 1024  # KB
            print(f"  - {table_name}.xlsx ({file_size:.1f} KB)")

if __name__ == "__main__":
    export_tables_to_excel()
