"""
Collector for Anthropic official documentation and blog updates
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collect_anthropic_updates():
    """
    Collect updates from Anthropic official sources
    Returns a list of articles/updates
    """
    updates = []

    # Scrape Anthropic news page directly (RSS is no longer available)
    try:
        news_updates = scrape_anthropic_news()
        updates.extend(news_updates)
    except Exception as e:
        logger.error(f"Error scraping Anthropic news: {e}")

    # Try to get updates from docs.anthropic.com
    try:
        docs_updates = check_docs_updates()
        updates.extend(docs_updates)
    except Exception as e:
        logger.error(f"Error checking docs: {e}")

    logger.info(f"Collected {len(updates)} Anthropic updates")
    return updates


def scrape_anthropic_news():
    """
    Scrape news directly from Anthropic website
    Only include news from the last 7 days
    """
    import re
    from dateutil import parser as date_parser

    updates = []
    url = 'https://www.anthropic.com/news'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    # Common category labels to exclude from titles
    category_labels = {'announcements', 'product', 'policy', 'research', 'company', 'safety'}

    # Only include news from last 14 days (to catch recent news reliably)
    cutoff_date = datetime.now() - timedelta(days=14)

    try:
        logger.info("Fetching Anthropic News page...")
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find news items - look for links with /news/ in href
            news_links = soup.find_all('a', href=re.compile(r'^/news/[^/]+$'))

            seen_urls = set()
            for link in news_links[:30]:  # Check first 30 links
                href = link.get('href', '')
                if href in seen_urls or href == '/news':
                    continue
                seen_urls.add(href)

                full_url = f"https://www.anthropic.com{href}"

                # Extract title from URL slug as fallback
                slug = href.replace('/news/', '')
                slug_title = slug.replace('-', ' ').title()

                # Try to find title - look for headline elements
                title = None
                for tag in ['h2', 'h3', 'h4', 'h5', 'h6']:
                    title_elem = link.find(tag)
                    if title_elem:
                        candidate = title_elem.get_text(strip=True)
                        # Skip if it's just a category label
                        if candidate.lower() not in category_labels and len(candidate) > 10:
                            title = candidate
                            break

                # If no good title found in headings, try span with class containing 'title'
                if not title:
                    title_spans = link.find_all('span')
                    for span in title_spans:
                        text = span.get_text(strip=True)
                        if text.lower() not in category_labels and len(text) > 15:
                            title = text
                            break

                # Use URL slug as last resort
                if not title or title.lower() in category_labels:
                    title = slug_title

                if not title or len(title) < 5:
                    continue

                # Try to find date and filter by recency
                date_elem = link.find('time')
                published = ''
                if date_elem:
                    published = date_elem.get_text(strip=True)
                    # Parse the date and check if it's recent
                    try:
                        pub_date = date_parser.parse(published)
                        if pub_date < cutoff_date:
                            logger.debug(f"Skipping old article: {title} ({published})")
                            continue
                    except:
                        # If we can't parse the date, skip to be safe
                        logger.debug(f"Could not parse date for: {title}")
                        continue
                else:
                    # No date found, skip this article
                    continue

                # Try to find summary/description
                summary_elem = link.find('p')
                summary = ''
                if summary_elem:
                    summary_text = summary_elem.get_text(strip=True)
                    # Make sure summary is not just the title repeated
                    if summary_text.lower() != title.lower():
                        summary = summary_text

                updates.append({
                    'title': title,
                    'url': full_url,
                    'summary': summary[:300] + '...' if len(summary) > 300 else summary,
                    'published': published,
                    'source': 'Anthropic News',
                    'category': 'official_updates'
                })

            logger.info(f"Found {len(updates)} recent news items from Anthropic (last 14 days)")

    except Exception as e:
        logger.error(f"Error scraping Anthropic news: {e}")

    return updates


def check_docs_updates():
    """
    Check for updates in Anthropic documentation by comparing page content hash
    """
    import hashlib
    import json
    from pathlib import Path

    updates = []
    cache_file = Path(__file__).parent.parent.parent / 'data' / 'docs_cache.json'

    # Load previous cache
    cache = {}
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
        except:
            cache = {}

    # Pages to monitor for changes
    docs_pages = [
        {
            'url': 'https://docs.anthropic.com/en/release-notes/overview',
            'name': 'API Release Notes'
        },
        {
            'url': 'https://docs.anthropic.com/en/docs/welcome',
            'name': 'Documentation Updates'
        }
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    for page in docs_pages:
        try:
            response = requests.get(page['url'], headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract main content text
                main_content = soup.find('main') or soup.find('article') or soup.body
                if main_content:
                    content_text = main_content.get_text(strip=True)
                    content_hash = hashlib.md5(content_text.encode()).hexdigest()

                    # Check if content changed
                    old_hash = cache.get(page['url'])
                    if old_hash is None:
                        # First time seeing this page, don't report as update
                        logger.info(f"First time caching: {page['name']}")
                    elif old_hash != content_hash:
                        # Content changed!
                        logger.info(f"Detected update: {page['name']}")

                        # Try to extract first heading or summary
                        first_heading = soup.find(['h2', 'h3'])
                        summary = first_heading.get_text(strip=True) if first_heading else 'New updates available'

                        updates.append({
                            'title': f"Anthropic {page['name']} Updated",
                            'url': page['url'],
                            'summary': f"Changes detected: {summary[:200]}",
                            'published': datetime.now().isoformat(),
                            'source': 'Anthropic Docs',
                            'category': 'official_updates'
                        })

                    # Update cache
                    cache[page['url']] = content_hash

        except Exception as e:
            logger.error(f"Error checking {page['name']}: {e}")

    # Save cache
    try:
        cache_file.parent.mkdir(exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

    return updates


if __name__ == '__main__':
    # Test the collector
    updates = collect_anthropic_updates()
    print(f"Found {len(updates)} updates:")
    for update in updates:
        print(f"  - {update['title']}")
