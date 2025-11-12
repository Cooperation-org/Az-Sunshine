"""
Simple Local SOI Scraper
Run this on your LOCAL MACHINE (laptop/desktop) where you can see the browser

Requirements:
    pip install playwright beautifulsoup4
    playwright install chromium

Usage:
    python local_scraper.py

Output:
    Creates soi_candidates.csv that you upload to server
"""

import asyncio
import csv
import re
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


# Target URLs from project spec
SOI_URLS = [
    "https://apps.arizona.vote/electioninfo/SOI/71",  # Primary
    "https://apps.arizona.vote/electioninfo/SOI/69",
    "https://apps.arizona.vote/electioninfo/SOI/68"
]


def parse_candidates(html, source_url):
    """Parse candidate data from HTML table"""
    soup = BeautifulSoup(html, 'html.parser')
    candidates = []
    
    # Find table rows
    rows = soup.select('table tbody tr, table tr')
    print(f"  Found {len(rows)} table rows")
    
    for row in rows:
        try:
            text = row.get_text(strip=True)
            
            # Skip empty or header rows
            if not text or len(text) < 5:
                continue
            if 'office' in text.lower() and 'candidate' in text.lower():
                continue
            
            cells = row.find_all('td')
            if len(cells) < 2:
                continue
            
            # Extract fields (Order: Office, Name, Party, Phone, Email)
            office = cells[0].get_text(strip=True) if len(cells) > 0 else ''
            name = cells[1].get_text(strip=True) if len(cells) > 1 else ''
            party = cells[2].get_text(strip=True) if len(cells) > 2 else ''
            phone = cells[3].get_text(strip=True) if len(cells) > 3 else ''
            
            # Extract email from anywhere in row text
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            email = email_match.group(0) if email_match else ''
            
            if name and len(name) > 2:
                candidates.append({
                    'name': name,
                    'office': office,
                    'party': party,
                    'phone': phone,
                    'email': email,
                    'source_url': source_url
                })
        except Exception as e:
            print(f"  ⚠️  Error parsing row: {e}")
            continue
    
    return candidates


async def scrape_with_browser():
    """Scrape SOI pages with visible browser"""
    all_candidates = []
    
    async with async_playwright() as p:
        print("\n" + "="*70)
        print("🌐 Launching Chrome Browser...")
        print("="*70)
        print("NOTE: You may need to solve Cloudflare challenges manually")
        print("The browser will open in a visible window\n")
        
        # Launch VISIBLE browser (not headless)
        browser = await p.chromium.launch(
            headless=False,  # IMPORTANT: Visible browser
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        
        page = await browser.new_page()
        
        for i, url in enumerate(SOI_URLS, 1):
            print("="*70)
            print(f"📄 Scraping Page {i}/{len(SOI_URLS)}")
            print(f"URL: {url}")
            print("="*70)
            
            try:
                print("⏳ Loading page...")
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Wait a bit for page to fully load
                await asyncio.sleep(3)
                
                # Check if Cloudflare challenge is present
                content = await page.content()
                if 'cloudflare' in content.lower() or 'verify you are human' in content.lower():
                    print("\n" + "!"*70)
                    print("⚠️  CLOUDFLARE CHALLENGE DETECTED")
                    print("!"*70)
                    print("Please solve the challenge in the browser window")
                    print("Press Enter in this terminal when the page loads...")
                    print("!"*70 + "\n")
                    input()
                    
                    # Wait a bit more after user confirms
                    await asyncio.sleep(2)
                
                # Get final page content
                html = await page.content()
                
                # Parse candidates
                print("📊 Parsing candidate data...")
                candidates = parse_candidates(html, url)
                print(f"✅ Found {len(candidates)} candidates")
                
                if candidates:
                    sample = candidates[0]
                    print(f"   Sample: {sample['name']} - {sample['office']}")
                
                all_candidates.extend(candidates)
                
                # Delay between pages
                if i < len(SOI_URLS):
                    print("\n⏳ Waiting 5 seconds before next page...\n")
                    await asyncio.sleep(5)
                
            except Exception as e:
                print(f"❌ Error scraping {url}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        await browser.close()
    
    return all_candidates


def save_to_csv(candidates, filename='soi_candidates.csv'):
    """Save candidates to CSV"""
    if not candidates:
        print("\n❌ No candidates to save")
        return False
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['name', 'office', 'party', 'phone', 'email', 'source_url']
        )
        writer.writeheader()
        writer.writerows(candidates)
    
    print(f"\n💾 Saved {len(candidates)} candidates to {filename}")
    return True


async def main():
    """Main execution"""
    print("="*70)
    print("🗳️  Arizona SOI Local Scraper")
    print("="*70)
    print("\nThis scraper will:")
    print("1. Open a visible Chrome browser")
    print("2. Navigate to Arizona SOI pages")
    print("3. Pause if Cloudflare challenge appears")
    print("4. Extract candidate data")
    print("5. Save to soi_candidates.csv")
    print("\nPress Enter to start...")
    print("="*70)
    
    input()
    
    # Scrape
    candidates = await scrape_with_browser()
    
    # Save results
    if save_to_csv(candidates):
        print("\n" + "="*70)
        print("✅ SCRAPING COMPLETE!")
        print("="*70)
        print(f"📊 Total candidates: {len(candidates)}")
        print(f"📁 File: soi_candidates.csv")
        print("\n" + "="*70)
        print("📋 NEXT STEPS:")
        print("="*70)
        print("1. Upload CSV to your server:")
        print("   scp soi_candidates.csv deploy@az-sunshine.app:/opt/az_sunshine/backend/data/")
        print("\n2. On the server, load into database:")
        print("   python manage.py load_soi_csv data/soi_candidates.csv --dry-run")
        print("   python manage.py load_soi_csv data/soi_candidates.csv")
        print("\n3. View in Django Admin:")
        print("   https://az-sunshine.app/admin/transparency/candidatestatementofinterest/")
        print("="*70)
    else:
        print("\n❌ Scraping failed - no data collected")


if __name__ == '__main__':
    asyncio.run(main())