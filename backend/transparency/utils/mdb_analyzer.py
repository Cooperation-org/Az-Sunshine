"""
Arizona Transparency - Claude API MDB Analysis Helper
Uses Claude to help map MDB data to Ben's architecture
"""

import anthropic
import os
import csv
import json

def read_csv_sample(csv_file, num_rows=5):
    """Read first few rows of a CSV file"""
    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            rows = []
            for i, row in enumerate(reader):
                if i >= num_rows:
                    break
                rows.append(row)
            return rows, reader.fieldnames
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        return None, None

def analyze_table_with_claude(client, table_name, headers, sample_data):
    """Use Claude to analyze a table and suggest mapping"""
    
    prompt = f"""I'm working on the Arizona Transparency Project to track campaign finance and independent expenditures.

I have a database table called "{table_name}" with these columns:
{', '.join(headers)}

Here are a few sample rows:
{json.dumps(sample_data, indent=2)}

Based on this architecture diagram description:
- Candidates: stores candidate info, races, party, compliance
- IE Committees: independent expenditure committees
- Entities: donors, lobbyists, staff, family members  
- Contributions: donations for/against candidates
- Expenses: spending for/against candidates (IE For/Against)
- Bills: legislative bills
- Actions: votes, statements, positions on bills

Questions:
1. What category does this "{table_name}" table likely belong to?
2. What are the key fields I should map to the Django models?
3. Are there any data quality issues I should watch for?
4. How does this relate to the Arizona SOS campaign finance data?

Please be concise and specific."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text

def compare_with_sos_data(client, table_data, sos_columns):
    """Compare MDB data structure with Arizona SOS website structure"""
    
    prompt = f"""I need to verify this campaign finance data matches the official Arizona SOS website.

The Arizona SOS "See the Money" website shows these columns for candidates:
- Name
- Candidate Committee  
- Office
- Party
- Income
- Expense
- Cash Balance
- IE For (Independent Expenditure supporting)
- IE Against (Independent Expenditure opposing)

My database table has these fields:
{', '.join(table_data)}

Questions:
1. Do these fields match the SOS structure?
2. What fields might be missing?
3. What fields might be additional/different?
4. How should I map between them?

Be specific about field name mappings."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text

def main():
    """Main execution"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   Claude API - MDB Analysis Assistant                      ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = input("Enter your Claude API key: ").strip()
    
    # Initialize Claude client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Get exported CSV directory
    csv_dir = input("Enter path to directory with exported CSV files (default: ./mdb_exports): ").strip()
    if not csv_dir:
        csv_dir = "./mdb_exports"
    
    if not os.path.exists(csv_dir):
        print(f"❌ Directory not found: {csv_dir}")
        print("Please run the MDB analyzer first to export tables.")
        return
    
    # Get list of CSV files
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print(f"❌ No CSV files found in {csv_dir}")
        return
    
    print(f"\n✓ Found {len(csv_files)} CSV files")
    print("\nAnalyzing each table with Claude...\n")
    
    # Arizona SOS columns for comparison
    sos_columns = ["Name", "Candidate Committee", "Office", "Party", "Income", 
                   "Expense", "Cash Balance", "IE For", "IE Against"]
    
    results = {}
    
    for csv_file in csv_files:
        table_name = os.path.splitext(csv_file)[0]
        print(f"\n{'='*60}")
        print(f"Analyzing: {table_name}")
        print(f"{'='*60}")
        
        # Read sample data
        sample_data, headers = read_csv_sample(os.path.join(csv_dir, csv_file))
        
        if not headers:
            print(f"❌ Could not read {csv_file}")
            continue
        
        print(f"\nColumns: {', '.join(headers)}")
        
        try:
            # Analyze with Claude
            print("\n🤖 Claude's Analysis:")
            print("-" * 60)
            analysis = analyze_table_with_claude(client, table_name, headers, sample_data)
            print(analysis)
            
            results[table_name] = {
                'headers': headers,
                'analysis': analysis
            }
            
            # Ask if this looks like candidate data
            if 'candidate' in table_name.lower() or 'filer' in table_name.lower():
                print("\n\n🔍 Comparing with Arizona SOS structure...")
                print("-" * 60)
                comparison = compare_with_sos_data(client, headers, sos_columns)
                print(comparison)
                results[table_name]['sos_comparison'] = comparison
            
        except Exception as e:
            print(f"❌ Error analyzing {table_name}: {e}")
        
        # Rate limiting - pause between requests
        import time
        time.sleep(1)
    
    # Save results
    output_file = "claude_analysis_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\n✓ Analysis complete! Results saved to {output_file}")
    print("\n📋 SUMMARY:")
    print("-" * 60)
    print(f"Analyzed {len(results)} tables")
    print(f"Review {output_file} for detailed mappings")
    print("\nNext steps:")
    print("1. Review Claude's suggestions for each table")
    print("2. Verify mappings match Ben's architecture diagram")
    print("3. Check data against Arizona SOS website")
    print("4. Create Django models based on these mappings")

if __name__ == "__main__":
    main()
