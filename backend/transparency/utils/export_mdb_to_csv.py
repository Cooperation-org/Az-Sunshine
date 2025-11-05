"""
Export MDB tables to CSV files for Claude analysis
"""

import subprocess
import os
import sys

def export_mdb_tables(mdb_file, output_dir="./mdb_exports"):
    """Export all tables from MDB to CSV files"""
    
    # Check if mdb-tools is installed
    try:
        subprocess.run(['mdb-tables', '--help'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("❌ mdb-tools not found!")
        print("\nInstall with:")
        print("  Ubuntu/Debian: sudo apt-get install mdb-tools")
        print("  Mac: brew install mdb-tools")
        sys.exit(1)
    
    if not os.path.exists(mdb_file):
        print(f"❌ MDB file not found: {mdb_file}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📂 Reading tables from: {mdb_file}")
    
    # Get list of tables
    result = subprocess.run(['mdb-tables', '-1', mdb_file], 
                          capture_output=True, text=True)
    
    tables = [t.strip() for t in result.stdout.strip().split('\n') if t.strip()]
    
    print(f"✓ Found {len(tables)} tables\n")
    
    # Export each table
    for table in tables:
        print(f"Exporting: {table}...", end=" ")
        csv_file = os.path.join(output_dir, f"{table}.csv")
        
        try:
            with open(csv_file, 'w') as f:
                subprocess.run(['mdb-export', mdb_file, table], 
                             stdout=f, check=True)
            print("✓")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✓ Exported {len(tables)} tables to {output_dir}")
    return output_dir

if __name__ == "__main__":
    mdb_file = input("Enter path to MDB file: ").strip().strip('"')
    output_dir = input("Export directory (default: ./mdb_exports): ").strip()
    
    if not output_dir:
        output_dir = "./mdb_exports"
    
    export_mdb_tables(mdb_file, output_dir)
