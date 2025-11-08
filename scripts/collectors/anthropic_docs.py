"""
Collector for Anthropic official documentation and blog updates
"""

import feedparser
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

    # RSS feeds to monitor
    rss_feeds = [
        {
            'url': 'https://www.anthropic.com/news/rss.xml',
            'source': 'Anthropic News'
        },
    ]

    # Collect from RSS feeds
    for feed_config in rss_feeds:
        try:
            logger.info(f"Fetching {feed_config['source']}...")
            feed = feedparser.parse(feed_config['url'])

            for entry in feed.entries[:10]:  # Limit to 10 most recent
                # Check if it's about Claude
                if 'claude' in entry.title.lower() or 'claude' in entry.get('summary', '').lower():
                    updates.append({
                        'title': entry.title,
                        'url': entry.link,
                        'summary': entry.get('summary', '')[:300] + '...' if len(entry.get('summary', '')) > 300 else entry.get('summary', ''),
                        'published': entry.get('published', ''),
                        'source': feed_config['source'],
                        'category': 'official_updates'
                    })
        except Exception as e:
            logger.error(f"Error fetching {feed_config['source']}: {e}")

    # Try to get updates from docs.anthropic.com
    try:
        docs_updates = check_docs_updates()
        updates.extend(docs_updates)
    except Exception as e:
        logger.error(f"Error checking docs: {e}")

    logger.info(f"Collected {len(updates)} Anthropic updates")
    return updates


def check_docs_updates():
    """
    Check for updates in Anthropic documentation
    """
    updates = []

    # Check release notes page
    try:
        url = 'https://docs.anthropic.com/en/release-notes/overview'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for recent updates (this is a simplified approach)
            # In practice, you'd want to compare with previous snapshots
            title = soup.find('h1')
            if title:
                updates.append({
                    'title': 'Claude API Release Notes',
                    'url': url,
                    'summary': 'Check the latest API updates and release notes',
                    'published': datetime.now().isoformat(),
                    'source': 'Anthropic Docs',
                    'category': 'official_updates'
                })
    except Exception as e:
        logger.error(f"Error checking release notes: {e}")

    return updates


if __name__ == '__main__':
    # Test the collector
    updates = collect_anthropic_updates()
    print(f"Found {len(updates)} updates:")
    for update in updates:
        print(f"  - {update['title']}")
