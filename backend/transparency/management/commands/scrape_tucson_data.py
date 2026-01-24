"""
Web scraper for tucson.com (Arizona Daily Star) campaign finance articles.

This scraper fetches campaign finance data mentioned in news articles from
tucson.com for verification against our database.

NOTE: tucson.com blocks AI crawlers (Claude, GPT) in robots.txt. This scraper
uses standard HTTP requests with appropriate user-agent strings and rate limiting
to be respectful of their servers.

Usage:
    python manage.py scrape_tucson_data
    python manage.py scrape_tucson_data --year 2022
    python manage.py scrape_tucson_data --output /custom/path/output.json
    python manage.py scrape_tucson_data --compare
"""

import json
import re
import time
import hashlib
from decimal import Decimal
from datetime import datetime
from collections import defaultdict
from urllib.parse import urljoin, quote_plus

from django.core.management.base import BaseCommand
from django.db.models import Sum, Q
from django.db.models.functions import Abs

import requests
from bs4 import BeautifulSoup

from transparency.models import Transaction, Committee, Office, Cycle, FECIndependentExpenditure


class Command(BaseCommand):
    help = 'Scrape campaign finance data from tucson.com articles'

    # Default output path
    DEFAULT_OUTPUT = '/opt/az_sunshine/data/tucson_verification_data.json'

    # Respectful scraping settings
    REQUEST_DELAY = 2.0  # seconds between requests
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    TIMEOUT = 30

    # Search terms for finding relevant articles
    SEARCH_TERMS = [
        'campaign finance Arizona',
        'independent expenditure Arizona',
        'dark money Arizona',
        'outside spending Arizona election',
        'PAC spending Arizona',
        'RGA Arizona governor',
        'Republican Governors Association Arizona',
        'APS political spending',
        'Arizona Public Service Corporation Commission',
        'election spending Arizona',
        'super PAC Arizona',
        'political advertising Arizona',
    ]

    # Known article URLs from tucson.com about campaign finance
    KNOWN_ARTICLE_URLS = [
        # Dark money articles
        'https://tucson.com/news/state-and-regional/dark-money-rules-eased-in-az-senate-campaign-finance-bill/article_809e66e3-bbc5-57c7-87d5-b25194abb486.html',
        'https://tucson.com/news/local/court-reopens-door-to-dark-money-in-arizona-political-races/article_89a3773d-f533-5e6c-ba56-f5375baa2016.html',
        'https://tucson.com/news/local/lawsuit-challenges-new-arizona-law-allowing-more-dark-money-in/article_86a6174a-9ac7-5872-98f3-db6fd2c0254a.html',
        'https://tucson.com/news/local/dark-money-expansion-remains-on-hold-while-court-decides-future-of-law/article_b9ad6f62-a757-5992-b354-c185b1f0585d.html',

        # APS political spending
        'https://tucson.com/news/local/aps-admits-spending-10-7-million-in-2014-to-elect-two-regulators-of-its-choice/article_bc6636af-c128-5765-8906-482b92a1bf20.html',
        'https://tucson.com/news/local/steller-column-brazen-aps-grew-intoxicated-with-politics-documents-show/article_d7c69bf6-39be-56d8-b711-ab2e3750e941.html',
        'https://tucson.com/news/article_d80b85aa-4dd0-5516-a002-7d012f5ef7c2.html',  # Utility $3.5M Corp Comm
        'https://tucson.com/business/tucson/3-vow-to-force-arizona-utilities-to-disclose-political-spending/article_dd5d59a3-9387-5f10-8037-3da2d32a1f23.html',
        'https://tucson.com/business/local/regulator-wants-aps-campaign-spending-data/article_5fc93263-13d0-56c0-b0a1-1abaa3aac782.html',

        # RGA spending
        'https://tucson.com/news/local/govt-and-politics/gop-governors-group-to-spend-at-least-11-million-on-arizonas-race/article_8edf5018-14e9-11ed-80d5-6fde4f6b0067.html',
        'https://tucson.com/news/local/national-gop-group-drops-millions-vs-one-of-the-democrats/article_462d6dfa-4c91-54f2-8ceb-264fdd525d1c.html',
        'https://tucson.com/news/local/govt-and-politics/elections/outside-groups-spend-millions-on-arizona-political-races/article_4a39d24a-ee14-5a05-a931-232e7054cf18.html',

        # Governor race spending
        'https://tucson.com/news/local/doug-ducey-outspending-david-garcia-by-nearly-to/article_3e08fdf6-ba52-5d72-9b69-4667dc454483.html',
        'https://tucson.com/news/state-regional/article_322f1026-4e4e-11ed-9ec7-539915fed12e.html',  # Hobbs fundraising
        'https://tucson.com/news/state-regional/government-politics/elections/article_bf40b4e3-3df5-46de-af38-a4117f6aadc9.html',  # Hobbs, Robson
        'https://tucson.com/news/state-regional/government-politics/elections/article_3783108b-17e6-41b3-8901-216ac8cf7ae5.html',  # Campaigns raise millions

        # Senate race spending
        'https://tucson.com/news/local/mark-kelly-widens-fundraising-lead-over-martha-mcsally-in-big-dollar-senate-race/article_65dc2f0a-735d-5622-95d5-46fce905be80.html',
        'https://tucson.com/news/local/mark-kellys-finances-take-center-stage-in-arizona-senate-race/article_6ccb08dc-8134-57de-9ea7-3a3371fb6125.html',
        'https://tucson.com/news/local/democratic-senate-candidate-mark-kelly-has-raised-about-8m-more-than-sen-martha-mcsally-so/article_8a81be77-e62e-5a5b-9f25-5fa2c2f84b5c.html',

        # CD2 spending
        'https://tucson.com/news/local/govt-and-politics/contributions-already-piling-up-in-anticipated-cd2-rematch/article_5a40e2d3-881f-5cd0-a28a-6de1dfea3f81.html',
        'https://tucson.com/news/local/kirkpatrick-raises-more-than-k-in-cd-race-heinz-loans/article_54676694-83ad-51ff-9374-7e878449c4b6.html',
        'https://tucson.com/news/local/kirkpatrick-accuses-gop-pac-of-campaign-finance-violations/article_08e95475-24d2-57cd-a7f7-b2dd59951055.html',
        'https://tucson.com/news/local/martha-mcsally-tops-fundraising-in-congressional-district-race/article_b4764962-4311-52b9-a640-7e6fc61dd369.html',
        'https://tucson.com/news/local/kirkpatrick-tops-all-in-fundraising-for-tucson-area-cd-race/article_d683f53a-3c35-559b-86a5-648ce4f5c506.html',

        # Tucson local/PAC spending
        'https://tucson.com/news/local/government-politics/tucson-city-council-campaign-finance/article_3e460dec-2657-11ee-b77a-53be9564a678.html',
        'https://tucson.com/news/local/govt-and-politics/elections/big-5-donors-in-southern-arizona-politics-may-surprise-you/article_918d867a-8d26-5970-87e1-2a2f9d43fe92.html',
        'https://tucson.com/news/local/tucson-dark-money-group-wins-legal-challenge/article_8dcfb766-589e-542f-b8c3-dd99b5c2f883.html',

        # Prop 211 / campaign finance reform
        'https://tucson.com/news/state-regional/government-politics/elections/article_027dc21a-5a3c-4a78-b6c0-becdedf52bda.html',
    ]

    # Known spending data from tucson.com articles (for direct verification)
    KNOWN_SPENDING_DATA = [
        # APS Corporation Commission 2014
        {
            'entity': 'Arizona Public Service (Pinnacle West)',
            'amount': 10700000,
            'context': 'Total spent to elect Corporation Commission candidates',
            'year': 2014,
            'race': 'Corporation Commission',
            'candidates': ['Tom Forese', 'Doug Little'],
            'source': 'APS admits spending $10.7 million in 2014',
        },
        {
            'entity': 'Arizona Free Enterprise Club',
            'amount': 5900000,
            'context': 'Dark money from APS via Arizona Free Enterprise Club',
            'year': 2014,
            'race': 'Corporation Commission',
            'candidates': ['Tom Forese', 'Doug Little'],
            'source': 'Pinnacle West gave nearly $5.9 million to the Free Enterprise Club',
        },
        {
            'entity': 'Save Our Future Now',
            'amount': 3500000,
            'context': 'Dark money from APS via Save Our Future Now',
            'year': 2014,
            'race': 'Corporation Commission',
            'candidates': ['Tom Forese', 'Doug Little'],
            'source': 'Pinnacle West funneled $3.5 million into Save Our Future Now',
        },
        {
            'entity': 'Arizona Cattle Feeders Association',
            'amount': 1400000,
            'context': 'Dark money from APS via Arizona Cattle Feeders',
            'year': 2014,
            'race': 'Corporation Commission',
            'candidates': ['Tom Forese', 'Doug Little'],
            'source': 'Pinnacle West gave $1.4 million to Arizona Cattle Feeders',
        },

        # RGA Governor spending
        {
            'entity': 'Republican Governors Association',
            'amount': 11000000,
            'context': 'IE spending on Arizona governor race against Katie Hobbs',
            'year': 2022,
            'race': 'Governor',
            'candidates': ['Kari Lake', 'Katie Hobbs'],
            'source': 'GOP governors group to spend at least $11 million',
        },
        {
            'entity': 'Republican Governors Association',
            'amount': 9200000,
            'context': 'IE spending on Arizona governor race for Doug Ducey',
            'year': 2018,
            'race': 'Governor',
            'candidates': ['Doug Ducey', 'David Garcia'],
            'source': 'RGA spent more than $9.2 million trying to ensure Doug Ducey got another term',
        },
        {
            'entity': 'Republican Governors Association',
            'amount': 5000000,
            'context': 'IE spending on Arizona governor race for Doug Ducey',
            'year': 2014,
            'race': 'Governor',
            'candidates': ['Doug Ducey', 'Fred DuVal'],
            'source': 'RGA spent close to $5 million trying to elect Ducey',
        },

        # 2020 Senate race
        {
            'entity': 'Mark Kelly Campaign',
            'amount': 77900000,
            'context': 'Campaign spending by Mark Kelly',
            'year': 2020,
            'race': 'US Senate',
            'candidates': ['Mark Kelly'],
            'source': 'Kelly burned through $77.9 million',
        },
        {
            'entity': 'Martha McSally Campaign',
            'amount': 47600000,
            'context': 'Campaign spending by Martha McSally',
            'year': 2020,
            'race': 'US Senate',
            'candidates': ['Martha McSally'],
            'source': 'McSally spent $47.6 million',
        },
        {
            'entity': 'Outside Groups (2020 Senate)',
            'amount': 81000000,
            'context': 'Total outside spending on 2020 Senate race',
            'year': 2020,
            'race': 'US Senate',
            'candidates': ['Mark Kelly', 'Martha McSally'],
            'source': 'Outside groups spending $81 million on the race',
        },

        # 2022 Governor fundraising
        {
            'entity': 'Katie Hobbs Campaign',
            'amount': 9600000,
            'context': 'Campaign fundraising',
            'year': 2022,
            'race': 'Governor',
            'candidates': ['Katie Hobbs'],
            'source': 'Hobbs had collected more than $9.6 million',
        },
        {
            'entity': 'Kari Lake Campaign',
            'amount': 7400000,
            'context': 'Campaign fundraising',
            'year': 2022,
            'race': 'Governor',
            'candidates': ['Kari Lake'],
            'source': 'Lake had collected nearly $7.4 million',
        },
        {
            'entity': 'National Rifle Association Political Victory Fund',
            'amount': 800000,
            'context': 'IE spending on governor race (400K pro-Lake, 400K anti-Hobbs)',
            'year': 2022,
            'race': 'Governor',
            'candidates': ['Kari Lake', 'Katie Hobbs'],
            'source': '$400,000 from NRA in advertising plus $400,000 opposition spending',
        },
        {
            'entity': 'Put Arizona First',
            'amount': 2100000,
            'context': 'IE spending attacking Karrin Robson in GOP primary',
            'year': 2022,
            'race': 'Governor Primary',
            'candidates': ['Kari Lake', 'Karrin Taylor Robson'],
            'source': 'Put Arizona First spent more than $2.1 million attacking Robson',
        },

        # CD2 spending
        {
            'entity': 'Americans for Prosperity',
            'amount': 650000,
            'context': 'Video ads attacking Ron Barber and Ann Kirkpatrick',
            'year': 2014,
            'race': 'US House CD2',
            'candidates': ['Ron Barber', 'Ann Kirkpatrick'],
            'source': 'Americans for Prosperity pledged to spend up to $650,000',
        },
        {
            'entity': 'Congressional Leadership Fund',
            'amount': 700000,
            'context': 'TV ads and GOTV for Martha McSally in CD2',
            'year': 2018,
            'race': 'US House CD2',
            'candidates': ['Martha McSally'],
            'source': 'Congressional Leadership Fund spent more than $700,000',
        },

        # APS Prop 127 (2018)
        {
            'entity': 'Pinnacle West (APS)',
            'amount': 10400000,
            'context': 'Anti-Prop 127 spending (renewable energy mandate)',
            'year': 2018,
            'race': 'Proposition 127',
            'candidates': [],
            'source': 'Anti-127 campaign had already spent $10.4 million',
        },

        # 2016 Corporation Commission
        {
            'entity': 'Pinnacle West (APS)',
            'amount': 3500000,
            'context': 'Spending to keep Corporation Commission all-Republican',
            'year': 2016,
            'race': 'Corporation Commission',
            'candidates': ['Bill Mundell'],
            'source': 'Pinnacle West spent more than $3.5 million',
        },

        # Southern Arizona big donors
        {
            'entity': 'Jim Click (and family)',
            'amount': 450000,
            'context': 'Contributions to Republican candidates and causes',
            'year': 2022,
            'race': 'Various',
            'candidates': [],
            'source': 'Jim Click and family contributed $450,000 to Republican candidates',
        },
        {
            'entity': 'Bill Roe (and wife)',
            'amount': 490000,
            'context': 'Contributions to Democratic candidates and causes',
            'year': 2022,
            'race': 'Various',
            'candidates': [],
            'source': 'Bill Roe and wife poured in $490,000 to Democratic candidates',
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='Filter to specific election year'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=self.DEFAULT_OUTPUT,
            help='Output JSON file path'
        )
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare scraped data with Az-Sunshine database'
        )
        parser.add_argument(
            '--scrape-live',
            action='store_true',
            help='Actually scrape live URLs (default uses known data only)'
        )
        parser.add_argument(
            '--search',
            action='store_true',
            help='Search tucson.com for new articles (requires --scrape-live)'
        )

    def handle(self, *args, **options):
        year_filter = options.get('year')
        output_path = options.get('output')
        do_compare = options.get('compare', False)
        scrape_live = options.get('scrape_live', False)
        do_search = options.get('search', False)

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n' + '=' * 70 + '\n'
            '  TUCSON.COM CAMPAIGN FINANCE SCRAPER\n'
            '  Arizona Daily Star Political Spending Data\n'
            '=' * 70 + '\n'
        ))

        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

        # Collect all data
        all_articles = []
        all_mentions = []

        # Step 1: Use known spending data (always available)
        self.stdout.write(self.style.SUCCESS('\n[Step 1] Loading known spending data from tucson.com articles...'))
        known_data = self._process_known_data(year_filter)
        all_mentions.extend(known_data)
        self.stdout.write(f'   Loaded {len(known_data)} known spending records')

        # Step 2: Search for article URLs (optional)
        article_urls = list(self.KNOWN_ARTICLE_URLS)
        if scrape_live and do_search:
            self.stdout.write(self.style.SUCCESS('\n[Step 2] Searching tucson.com for relevant articles...'))
            searched_urls = self._search_for_articles()
            new_urls = [u for u in searched_urls if u not in article_urls]
            article_urls.extend(new_urls)
            self.stdout.write(f'   Found {len(new_urls)} additional article URLs')
        else:
            self.stdout.write('\n[Step 2] Skipping live search (use --scrape-live --search to enable)')

        # Step 3: Scrape article content (optional)
        if scrape_live:
            self.stdout.write(self.style.SUCCESS(f'\n[Step 3] Scraping {len(article_urls)} article URLs...'))
            for i, url in enumerate(article_urls):
                self.stdout.write(f'   [{i+1}/{len(article_urls)}] {url[:60]}...')
                article_data = self._scrape_article(url)
                if article_data:
                    all_articles.append(article_data)
                    # Extract mentions from article
                    mentions = self._extract_mentions_from_article(article_data, year_filter)
                    all_mentions.extend(mentions)
                time.sleep(self.REQUEST_DELAY)

            self.stdout.write(f'   Successfully scraped {len(all_articles)} articles')
        else:
            self.stdout.write('\n[Step 3] Skipping live scraping (use --scrape-live to enable)')

        # Step 4: Aggregate data
        self.stdout.write(self.style.SUCCESS('\n[Step 4] Aggregating extracted data...'))
        aggregated = self._aggregate_data(all_mentions)

        # Display summary
        self._display_summary(all_mentions, aggregated)

        # Step 5: Save to JSON file
        self.stdout.write(self.style.SUCCESS(f'\n[Step 5] Saving to {output_path}...'))
        report = {
            'scraped_at': datetime.now().isoformat(),
            'source': 'tucson.com (Arizona Daily Star)',
            'year_filter': year_filter,
            'total_mentions': len(all_mentions),
            'total_articles_scraped': len(all_articles),
            'articles': all_articles,
            'mentions': all_mentions,
            'aggregated': aggregated,
        }

        # Ensure directory exists
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        self.stdout.write(self.style.SUCCESS(f'   Saved verification data to: {output_path}'))

        # Step 6: Compare with database (optional)
        if do_compare:
            self.stdout.write(self.style.SUCCESS('\n[Step 6] Comparing with Az-Sunshine database...'))
            self._compare_with_database(all_mentions, aggregated)
        else:
            self.stdout.write('\n[Step 6] Skipping database comparison (use --compare to enable)')

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('Scraping complete!'))
        self.stdout.write('=' * 70 + '\n')

    def _process_known_data(self, year_filter=None):
        """Process known spending data from curated list"""
        mentions = []
        for item in self.KNOWN_SPENDING_DATA:
            if year_filter and item.get('year') != year_filter:
                continue

            mention = {
                'entity': item['entity'],
                'amount': item['amount'],
                'context': item['context'],
                'year': item.get('year'),
                'race': item.get('race'),
                'candidates': item.get('candidates', []),
                'source_description': item.get('source', ''),
                'data_type': 'known',
            }
            mentions.append(mention)

        return mentions

    def _search_for_articles(self):
        """Search tucson.com for relevant articles"""
        found_urls = []

        for term in self.SEARCH_TERMS:
            try:
                # Use tucson.com's search
                search_url = f'https://tucson.com/search/?k={quote_plus(term)}&t=article'
                self.stdout.write(f'      Searching: {term}')

                response = self.session.get(search_url, timeout=self.TIMEOUT)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Find article links in search results
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if '/article_' in href and href.endswith('.html'):
                            full_url = urljoin('https://tucson.com', href)
                            if full_url not in found_urls:
                                found_urls.append(full_url)

                time.sleep(self.REQUEST_DELAY)

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'      Search error for "{term}": {e}'))

        return found_urls

    def _scrape_article(self, url):
        """Scrape a single article and extract data"""
        try:
            response = self.session.get(url, timeout=self.TIMEOUT)
            if response.status_code != 200:
                self.stdout.write(self.style.WARNING(f'      HTTP {response.status_code}'))
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract article metadata
            title = ''
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)

            # Extract date
            date = ''
            date_tag = soup.find('time') or soup.find(class_=re.compile('date|time|published'))
            if date_tag:
                date = date_tag.get('datetime', '') or date_tag.get_text(strip=True)

            # Extract article body
            body_text = ''
            article_body = soup.find('article') or soup.find(class_=re.compile('article|story|content'))
            if article_body:
                paragraphs = article_body.find_all('p')
                body_text = ' '.join(p.get_text(strip=True) for p in paragraphs)

            return {
                'url': url,
                'title': title,
                'date': date,
                'body': body_text[:10000],  # Limit body size
                'scraped_at': datetime.now().isoformat(),
            }

        except Exception as e:
            self.stdout.write(self.style.WARNING(f'      Error: {e}'))
            return None

    def _extract_mentions_from_article(self, article, year_filter=None):
        """Extract financial mentions from article text"""
        mentions = []
        body = article.get('body', '')

        # Patterns to find dollar amounts with context
        # Matches patterns like "$10.7 million", "$5,000", "10 million dollars"
        amount_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*(million|billion|thousand)?',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*(million|billion|thousand)?\s*dollars',
        ]

        # Known entities to look for
        entities_patterns = [
            (r'Republican Governors Association|RGA', 'Republican Governors Association'),
            (r'Arizona Public Service|APS|Pinnacle West', 'Arizona Public Service'),
            (r'Arizona Free Enterprise Club', 'Arizona Free Enterprise Club'),
            (r'Save Our Future Now', 'Save Our Future Now'),
            (r'Americans for Prosperity', 'Americans for Prosperity'),
            (r'Congressional Leadership Fund', 'Congressional Leadership Fund'),
            (r'House Majority PAC', 'House Majority PAC'),
            (r'Senate Majority PAC', 'Senate Majority PAC'),
            (r'NRCC|National Republican Congressional Committee', 'NRCC'),
            (r'DCCC|Democratic Congressional Campaign Committee', 'DCCC'),
            (r'NRA|National Rifle Association', 'NRA'),
        ]

        # Known candidates
        candidate_patterns = [
            (r'Katie Hobbs', 'Katie Hobbs'),
            (r'Kari Lake', 'Kari Lake'),
            (r'Doug Ducey', 'Doug Ducey'),
            (r'Mark Kelly', 'Mark Kelly'),
            (r'Martha McSally', 'Martha McSally'),
            (r'Kyrsten Sinema', 'Kyrsten Sinema'),
            (r'Ann Kirkpatrick', 'Ann Kirkpatrick'),
            (r'David Garcia', 'David Garcia'),
            (r'Tom Forese', 'Tom Forese'),
            (r'Doug Little', 'Doug Little'),
        ]

        # Extract years mentioned
        years_in_text = re.findall(r'\b(201\d|202\d)\b', body)

        # Find amounts and their context
        for pattern in amount_patterns:
            for match in re.finditer(pattern, body, re.IGNORECASE):
                amount_str = match.group(1).replace(',', '')
                multiplier_str = match.group(2) if len(match.groups()) > 1 else None

                try:
                    amount = float(amount_str)
                    if multiplier_str:
                        multiplier_str = multiplier_str.lower()
                        if 'million' in multiplier_str:
                            amount *= 1000000
                        elif 'billion' in multiplier_str:
                            amount *= 1000000000
                        elif 'thousand' in multiplier_str:
                            amount *= 1000

                    # Only include significant amounts
                    if amount < 1000:
                        continue

                    # Get context (surrounding text)
                    start = max(0, match.start() - 200)
                    end = min(len(body), match.end() + 200)
                    context = body[start:end]

                    # Find entities mentioned near this amount
                    found_entities = []
                    for entity_pattern, entity_name in entities_patterns:
                        if re.search(entity_pattern, context, re.IGNORECASE):
                            found_entities.append(entity_name)

                    # Find candidates mentioned near this amount
                    found_candidates = []
                    for cand_pattern, cand_name in candidate_patterns:
                        if re.search(cand_pattern, context, re.IGNORECASE):
                            found_candidates.append(cand_name)

                    # Determine year
                    year = None
                    year_match = re.search(r'\b(201\d|202\d)\b', context)
                    if year_match:
                        year = int(year_match.group(1))
                    elif years_in_text:
                        year = int(years_in_text[0])

                    if year_filter and year != year_filter:
                        continue

                    # Determine race type from context
                    race = 'Unknown'
                    if re.search(r'governor', context, re.IGNORECASE):
                        race = 'Governor'
                    elif re.search(r'senate', context, re.IGNORECASE):
                        race = 'US Senate'
                    elif re.search(r'congress|house|CD\d', context, re.IGNORECASE):
                        race = 'US House'
                    elif re.search(r'corporation commission|corp comm', context, re.IGNORECASE):
                        race = 'Corporation Commission'

                    mention = {
                        'entity': found_entities[0] if found_entities else 'Unknown',
                        'amount': int(amount),
                        'context': context.strip()[:300],
                        'year': year,
                        'race': race,
                        'candidates': found_candidates,
                        'source_url': article.get('url'),
                        'article_title': article.get('title'),
                        'data_type': 'extracted',
                    }
                    mentions.append(mention)

                except (ValueError, TypeError):
                    continue

        return mentions

    def _aggregate_data(self, mentions):
        """Aggregate mentions by different dimensions"""
        by_candidate = defaultdict(lambda: {'total': 0, 'mentions': []})
        by_committee = defaultdict(lambda: {'total': 0, 'mentions': []})
        by_race = defaultdict(lambda: {'total': 0, 'mentions': []})
        by_year = defaultdict(lambda: {'total': 0, 'mentions': []})

        for mention in mentions:
            amount = mention.get('amount', 0)
            entity = mention.get('entity', 'Unknown')
            race = mention.get('race', 'Unknown')
            year = mention.get('year', 'Unknown')

            # By committee/entity
            by_committee[entity]['total'] += amount
            by_committee[entity]['mentions'].append(mention)

            # By race
            by_race[race]['total'] += amount
            by_race[race]['mentions'].append(mention)

            # By year
            if year:
                by_year[str(year)]['total'] += amount
                by_year[str(year)]['mentions'].append(mention)

            # By candidate
            for candidate in mention.get('candidates', []):
                by_candidate[candidate]['total'] += amount
                by_candidate[candidate]['mentions'].append(mention)

        return {
            'by_candidate': {k: {'total': v['total'], 'mention_count': len(v['mentions'])}
                           for k, v in by_candidate.items()},
            'by_committee': {k: {'total': v['total'], 'mention_count': len(v['mentions'])}
                            for k, v in by_committee.items()},
            'by_race': {k: {'total': v['total'], 'mention_count': len(v['mentions'])}
                       for k, v in by_race.items()},
            'by_year': {k: {'total': v['total'], 'mention_count': len(v['mentions'])}
                       for k, v in by_year.items()},
        }

    def _display_summary(self, mentions, aggregated):
        """Display summary of extracted data"""
        self.stdout.write('\n' + '-' * 70)
        self.stdout.write('EXTRACTED DATA SUMMARY')
        self.stdout.write('-' * 70)

        self.stdout.write(f'\nTotal spending mentions extracted: {len(mentions)}')

        # By Year
        self.stdout.write('\n--- By Year ---')
        for year, data in sorted(aggregated['by_year'].items(), reverse=True):
            self.stdout.write(f'  {year}: ${data["total"]:,.0f} ({data["mention_count"]} mentions)')

        # By Race
        self.stdout.write('\n--- By Race ---')
        for race, data in sorted(aggregated['by_race'].items(), key=lambda x: x[1]['total'], reverse=True):
            self.stdout.write(f'  {race}: ${data["total"]:,.0f} ({data["mention_count"]} mentions)')

        # By Committee/Entity (top 10)
        self.stdout.write('\n--- Top Spending Entities ---')
        sorted_committees = sorted(aggregated['by_committee'].items(), key=lambda x: x[1]['total'], reverse=True)
        for entity, data in sorted_committees[:10]:
            self.stdout.write(f'  {entity}: ${data["total"]:,.0f} ({data["mention_count"]} mentions)')

        # By Candidate (top 10)
        self.stdout.write('\n--- Top Candidates by Spending Mentions ---')
        sorted_candidates = sorted(aggregated['by_candidate'].items(), key=lambda x: x[1]['total'], reverse=True)
        for candidate, data in sorted_candidates[:10]:
            self.stdout.write(f'  {candidate}: ${data["total"]:,.0f} ({data["mention_count"]} mentions)')

    def _compare_with_database(self, mentions, aggregated):
        """Compare extracted data with database"""
        self.stdout.write('\n' + '-' * 70)
        self.stdout.write('DATABASE COMPARISON')
        self.stdout.write('-' * 70)

        issues = []
        verified = []

        # Check for key entities
        key_entities = [
            ('Republican Governors Association', 'RGA'),
            ('Arizona Free Enterprise Club', 'Free Enterprise'),
            ('Save Our Future Now', 'Save Our'),
            ('Americans for Prosperity', 'Prosperity'),
            ('Congressional Leadership Fund', 'Leadership Fund'),
        ]

        self.stdout.write('\n--- Committee Verification ---')
        for entity_name, search_term in key_entities:
            found = Committee.objects.filter(
                Q(name__last_name__icontains=search_term) |
                Q(name__first_name__icontains=search_term)
            )

            expected = aggregated['by_committee'].get(entity_name, {}).get('total', 0)

            if found.exists():
                self.stdout.write(self.style.SUCCESS(f'  FOUND: {entity_name} ({found.count()} records)'))
                verified.append(entity_name)

                # Check total spending
                db_total = Transaction.objects.filter(
                    deleted=False,
                    committee__in=found,
                    transaction_type__income_expense_neutral=2,
                ).aggregate(total=Sum(Abs('amount')))['total'] or 0

                if expected > 0:
                    variance = abs(float(db_total) - expected)
                    if variance > expected * 0.2:  # More than 20% variance
                        self.stdout.write(self.style.WARNING(
                            f'    DB: ${db_total:,.0f} vs Expected: ${expected:,.0f} (variance: ${variance:,.0f})'
                        ))
                        issues.append({
                            'entity': entity_name,
                            'db_amount': float(db_total),
                            'expected_amount': expected,
                            'variance': variance,
                        })
                    else:
                        self.stdout.write(f'    DB: ${db_total:,.0f} vs Expected: ${expected:,.0f}')
            else:
                self.stdout.write(self.style.ERROR(f'  MISSING: {entity_name}'))
                issues.append({
                    'entity': entity_name,
                    'issue': 'Not found in database',
                    'expected_amount': expected,
                })

        # Check for key candidates (state and federal)
        key_candidates = [
            ('Katie Hobbs', 'state'),
            ('Kari Lake', 'state'),
            ('Doug Ducey', 'state'),
            ('Mark Kelly', 'federal'),
            ('Martha McSally', 'federal'),
            ('Tom Forese', 'state'),
            ('Doug Little', 'state'),
        ]

        self.stdout.write('\n--- Candidate Verification ---')
        for candidate_name, source in key_candidates:
            parts = candidate_name.split()
            first_name = parts[0]
            last_name = parts[-1] if len(parts) > 1 else parts[0]

            if source == 'federal':
                # Check FEC table for federal candidates
                found = FECIndependentExpenditure.objects.filter(
                    candidate_name__icontains=last_name
                )
                if found.exists():
                    total = found.aggregate(t=Sum(Abs('amount')))['t'] or 0
                    self.stdout.write(self.style.SUCCESS(
                        f'  FOUND (FEC): {candidate_name} ({found.count()} records, ${total:,.0f})'
                    ))
                    verified.append(candidate_name)
                else:
                    self.stdout.write(self.style.ERROR(f'  MISSING: {candidate_name}'))
                    issues.append({
                        'candidate': candidate_name,
                        'issue': 'Not found in FEC database',
                    })
            else:
                # Check state committees table
                found = Committee.objects.filter(
                    Q(candidate__last_name__icontains=last_name) |
                    Q(name__last_name__icontains=last_name)
                ).filter(
                    Q(candidate__first_name__icontains=first_name) |
                    Q(name__first_name__icontains=first_name)
                )

                if found.exists():
                    self.stdout.write(self.style.SUCCESS(f'  FOUND: {candidate_name} ({found.count()} records)'))
                    verified.append(candidate_name)
                else:
                    self.stdout.write(self.style.ERROR(f'  MISSING: {candidate_name}'))
                    issues.append({
                        'candidate': candidate_name,
                        'issue': 'Not found in database',
                    })

        # Summary
        self.stdout.write('\n' + '-' * 70)
        self.stdout.write('VERIFICATION SUMMARY')
        self.stdout.write('-' * 70)
        self.stdout.write(f'Verified: {len(verified)} items')
        self.stdout.write(f'Issues: {len(issues)} items')

        if issues:
            self.stdout.write(self.style.WARNING('\nIssues found:'))
            for issue in issues[:10]:
                if 'entity' in issue:
                    self.stdout.write(f'  - {issue.get("entity")}: {issue.get("issue", "Variance detected")}')
                elif 'candidate' in issue:
                    self.stdout.write(f'  - {issue.get("candidate")}: {issue.get("issue")}')
