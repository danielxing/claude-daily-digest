"""
Collector for Dev.to articles about Claude/Anthropic
Uses public API - no authentication required
"""

import requests
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEVTO_API = "https://dev.to/api/articles"


def collect_devto_articles():
    """
    Collect Claude-related articles from Dev.to
    Returns a list of articles
    """
    articles = []

    # Search tags and queries
    search_params = [
        {'tag': 'claude'},
        {'tag': 'anthropic'},
        {'tag': 'ai', 'per_page': 50},  # More general, will filter
        {'tag': 'llm', 'per_page': 50},
    ]

    # Cutoff for recent articles (14 days)
    cutoff_date = datetime.now() - timedelta(days=14)

    seen_ids = set()

    for params in search_params:
        try:
            tag = params.get('tag', '')
            logger.info(f"Fetching Dev.to articles with tag: {tag}")

            request_params = {
                'per_page': params.get('per_page', 30),
            }
            if tag:
                request_params['tag'] = tag

            response = requests.get(DEVTO_API, params=request_params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                for article in data:
                    article_id = article.get('id')

                    # Skip duplicates
                    if article_id in seen_ids:
                        continue
                    seen_ids.add(article_id)

                    title = article.get('title', '')
                    description = article.get('description', '')
                    content = (title + ' ' + description).lower()

                    # Filter for Claude-related content
                    claude_keywords = ['claude', 'anthropic', 'sonnet', 'opus', 'haiku']
                    if tag not in ['claude', 'anthropic']:
                        if not any(kw in content for kw in claude_keywords):
                            continue

                    # Check publication date
                    published_str = article.get('published_at', '')
                    if published_str:
                        try:
                            # Parse ISO format date
                            published_date = datetime.fromisoformat(
                                published_str.replace('Z', '+00:00')
                            ).replace(tzinfo=None)

                            if published_date < cutoff_date:
                                continue
                        except:
                            pass

                    # Determine category based on content
                    category = 'blog_posts'
                    content_lower = content.lower()
                    tags = [t.lower() for t in article.get('tag_list', [])]

                    if any(kw in content_lower or kw in tags for kw in
                           ['tutorial', 'guide', 'how to', 'tips', 'best practice']):
                        category = 'tutorials_and_tips'
                    elif any(kw in content_lower for kw in
                             ['claude code', 'terminal', 'cli', 'vscode', 'coding']):
                        category = 'claude_code'
                    elif any(kw in content_lower for kw in
                             ['project', 'built', 'created', 'workflow', 'use case']):
                        category = 'use_cases'

                    articles.append({
                        'title': title,
                        'url': article.get('url', ''),
                        'summary': description[:300] if description else '',
                        'published': published_str,
                        'source': 'Dev.to',
                        'category': category,
                        'author': article.get('user', {}).get('name', 'Unknown'),
                        'engagement': {
                            'reactions': article.get('public_reactions_count', 0),
                            'comments': article.get('comments_count', 0)
                        },
                        'tags': article.get('tag_list', [])
                    })

            else:
                logger.warning(f"Dev.to API returned {response.status_code}")

        except Exception as e:
            logger.error(f"Error fetching Dev.to articles: {e}")

    # Sort by engagement
    articles.sort(
        key=lambda x: x['engagement']['reactions'] + x['engagement']['comments'] * 2,
        reverse=True
    )

    # Limit to top 15
    articles = articles[:15]

    logger.info(f"Collected {len(articles)} Dev.to articles")
    return articles


def search_devto_tutorials():
    """
    Search specifically for Claude tutorials on Dev.to
    """
    tutorials = []

    search_queries = [
        'claude tutorial',
        'claude api guide',
        'anthropic tutorial',
        'claude code',
    ]

    cutoff_date = datetime.now() - timedelta(days=30)  # Wider range for tutorials
    seen_ids = set()

    for query in search_queries:
        try:
            logger.info(f"Searching Dev.to for: {query}")

            # Dev.to doesn't have a search API, so we use Google site search alternative
            # For now, we'll rely on tag-based collection
            # TODO: Could add web scraping of dev.to/search if needed

            pass

        except Exception as e:
            logger.error(f"Error searching Dev.to for '{query}': {e}")

    return tutorials


if __name__ == '__main__':
    # Test the collector
    print("Testing Dev.to collector...")

    articles = collect_devto_articles()
    print(f"\nFound {len(articles)} articles:")
    for a in articles[:5]:
        print(f"  - [{a['category']}] {a['title'][:50]}...")
        print(f"    By {a['author']} | {a['engagement']['reactions']} reactions")
        print(f"    Tags: {', '.join(a['tags'][:5])}")
        print()
