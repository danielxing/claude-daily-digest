"""
Collector for Hacker News discussions about Claude/Anthropic
Uses the Algolia HN Search API - no authentication required
"""

import requests
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Algolia HN Search API
HN_SEARCH_API = "https://hn.algolia.com/api/v1/search"


def collect_hackernews_discussions():
    """
    Collect Claude-related discussions from Hacker News
    Returns a list of posts/stories
    """
    discussions = []

    search_queries = [
        'claude anthropic',
        'claude code',
        'anthropic ai',
        'claude api',
    ]

    # Only include posts from last 14 days
    cutoff_timestamp = int((datetime.now() - timedelta(days=14)).timestamp())

    seen_ids = set()

    for query in search_queries:
        try:
            logger.info(f"Searching HN for: {query}")

            params = {
                'query': query,
                'tags': 'story',  # Only stories, not comments
                'numericFilters': f'created_at_i>{cutoff_timestamp}',
                'hitsPerPage': 20,
            }

            response = requests.get(HN_SEARCH_API, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                for hit in data.get('hits', []):
                    story_id = hit.get('objectID')

                    # Skip duplicates
                    if story_id in seen_ids:
                        continue
                    seen_ids.add(story_id)

                    title = hit.get('title', '')
                    url = hit.get('url', '')
                    points = hit.get('points', 0)
                    num_comments = hit.get('num_comments', 0)
                    created_at = hit.get('created_at', '')

                    # HN discussion URL
                    hn_url = f"https://news.ycombinator.com/item?id={story_id}"

                    # Use external URL if available, otherwise HN discussion
                    link = url if url else hn_url

                    # Filter by minimum engagement (at least 5 points or 3 comments)
                    if points < 5 and num_comments < 3:
                        continue

                    discussions.append({
                        'title': title,
                        'url': link,
                        'hn_url': hn_url,
                        'summary': f"{points} points, {num_comments} comments on HN",
                        'published': created_at,
                        'source': 'Hacker News',
                        'category': 'community_discussions',
                        'engagement': {
                            'points': points,
                            'comments': num_comments
                        }
                    })
            else:
                logger.warning(f"HN API returned {response.status_code} for query: {query}")

        except Exception as e:
            logger.error(f"Error searching HN for '{query}': {e}")

    # Sort by engagement (points + comments)
    discussions.sort(
        key=lambda x: x['engagement']['points'] + x['engagement']['comments'],
        reverse=True
    )

    # Limit to top 15
    discussions = discussions[:15]

    logger.info(f"Collected {len(discussions)} Hacker News discussions")
    return discussions


def collect_hn_claude_code_posts():
    """
    Specifically collect Claude Code related discussions
    """
    posts = []

    queries = [
        '"claude code"',
        'claude terminal',
        'claude cli',
        'anthropic mcp',
    ]

    cutoff_timestamp = int((datetime.now() - timedelta(days=14)).timestamp())
    seen_ids = set()

    for query in queries:
        try:
            params = {
                'query': query,
                'tags': '(story,comment)',  # Both stories and comments
                'numericFilters': f'created_at_i>{cutoff_timestamp}',
                'hitsPerPage': 15,
            }

            response = requests.get(HN_SEARCH_API, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                for hit in data.get('hits', []):
                    obj_id = hit.get('objectID')
                    if obj_id in seen_ids:
                        continue
                    seen_ids.add(obj_id)

                    # Handle both stories and comments
                    if hit.get('title'):
                        # It's a story
                        title = hit['title']
                        story_id = obj_id
                    else:
                        # It's a comment, get parent story
                        title = hit.get('story_title', 'HN Discussion')
                        story_id = hit.get('story_id', obj_id)

                    hn_url = f"https://news.ycombinator.com/item?id={story_id}"
                    points = hit.get('points', 0) or 0

                    posts.append({
                        'title': title,
                        'url': hn_url,
                        'summary': f"Claude Code discussion on HN",
                        'published': hit.get('created_at', ''),
                        'source': 'Hacker News',
                        'category': 'claude_code',
                        'engagement': {'points': points}
                    })

        except Exception as e:
            logger.error(f"Error searching HN Claude Code for '{query}': {e}")

    # Remove duplicates by URL and limit
    seen_urls = set()
    unique_posts = []
    for post in posts:
        if post['url'] not in seen_urls:
            seen_urls.add(post['url'])
            unique_posts.append(post)

    return unique_posts[:10]


if __name__ == '__main__':
    # Test the collector
    print("Testing Hacker News collector...")

    discussions = collect_hackernews_discussions()
    print(f"\nFound {len(discussions)} general discussions:")
    for d in discussions[:5]:
        print(f"  - {d['title']}")
        print(f"    {d['summary']} | {d['hn_url']}")

    print("\n" + "="*50)

    claude_code = collect_hn_claude_code_posts()
    print(f"\nFound {len(claude_code)} Claude Code posts:")
    for p in claude_code[:5]:
        print(f"  - {p['title']}")
        print(f"    {p['url']}")
