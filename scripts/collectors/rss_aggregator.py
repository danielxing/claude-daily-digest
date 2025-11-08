"""
RSS aggregator for tech blogs and articles about Claude
"""

import feedparser
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collect_blog_posts():
    """
    Collect Claude-related blog posts from various sources
    Returns a list of blog posts
    """
    articles = []

    # Tech blogs and news sources
    rss_feeds = [
        {
            'url': 'https://simonwillison.net/atom/everything/',
            'source': 'Simon Willison'
        },
        {
            'url': 'https://www.technologyreview.com/feed/',
            'source': 'MIT Technology Review'
        },
        {
            'url': 'https://techcrunch.com/feed/',
            'source': 'TechCrunch'
        },
        {
            'url': 'https://www.theverge.com/rss/index.xml',
            'source': 'The Verge'
        },
    ]

    for feed_config in rss_feeds:
        try:
            logger.info(f"Fetching {feed_config['source']}...")
            feed = feedparser.parse(feed_config['url'])

            for entry in feed.entries[:20]:  # Check 20 most recent
                # Filter for Claude-related content
                title_lower = entry.title.lower()
                summary_lower = entry.get('summary', '').lower()

                if any(keyword in title_lower or keyword in summary_lower
                       for keyword in ['claude', 'anthropic']):

                    # Check if it's recent (last 7 days)
                    published_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published_date = datetime(*entry.updated_parsed[:6])

                    # Only include if recent or no date available
                    if not published_date or (datetime.now() - published_date) < timedelta(days=7):
                        articles.append({
                            'title': entry.title,
                            'url': entry.link,
                            'summary': entry.get('summary', '')[:300] + '...' if len(entry.get('summary', '')) > 300 else entry.get('summary', ''),
                            'published': entry.get('published', entry.get('updated', '')),
                            'source': feed_config['source'],
                            'category': 'blog_posts'
                        })

        except Exception as e:
            logger.error(f"Error fetching {feed_config['source']}: {e}")

    logger.info(f"Collected {len(articles)} blog posts")
    return articles


def collect_community_content():
    """
    Collect content from AI/ML community sites
    This is a placeholder for potential future expansion
    """
    content = []

    # Could add:
    # - Hacker News API for Claude discussions
    # - Dev.to articles
    # - Medium publications
    # - YouTube channels (via RSS)

    return content


if __name__ == '__main__':
    # Test the collector
    posts = collect_blog_posts()
    print(f"Found {len(posts)} blog posts:")
    for post in posts[:5]:
        print(f"  - {post['title']} ({post['source']})")
