"""
Collector for Reddit discussions about Claude/Anthropic
Requires Reddit OAuth credentials (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
"""

import os
import requests
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reddit subreddits to monitor
SUBREDDITS = [
    'ClaudeAI',          # Main Claude community
    'ChatGPTCoding',     # Coding with AI (includes Claude)
    'LocalLLaMA',        # LLM discussions (Claude comparisons)
    'artificial',        # AI news
]

# Relevant keywords for filtering
CLAUDE_KEYWORDS = [
    'claude', 'anthropic', 'claude code', 'sonnet', 'opus', 'haiku',
    'claude api', 'mcp', 'model context protocol'
]


def get_reddit_token():
    """
    Get Reddit OAuth token using client credentials
    """
    client_id = os.environ.get('REDDIT_CLIENT_ID')
    client_secret = os.environ.get('REDDIT_CLIENT_SECRET')

    if not client_id or not client_secret:
        logger.warning("Reddit credentials not found. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
        return None

    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    headers = {'User-Agent': 'ClaudeDailyDigest/1.0'}
    data = {'grant_type': 'client_credentials'}

    try:
        response = requests.post(
            'https://www.reddit.com/api/v1/access_token',
            auth=auth,
            headers=headers,
            data=data,
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            logger.error(f"Reddit auth failed: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Reddit auth error: {e}")
        return None


def collect_reddit_posts():
    """
    Collect Claude-related posts from Reddit
    Returns a list of posts
    """
    posts = []

    token = get_reddit_token()
    if not token:
        logger.warning("Skipping Reddit collection - no auth token")
        return posts

    headers = {
        'Authorization': f'Bearer {token}',
        'User-Agent': 'ClaudeDailyDigest/1.0'
    }

    # Cutoff for recent posts (14 days)
    cutoff_time = datetime.now() - timedelta(days=14)
    cutoff_timestamp = cutoff_time.timestamp()

    seen_ids = set()

    for subreddit in SUBREDDITS:
        try:
            logger.info(f"Fetching r/{subreddit}...")

            # Get hot and new posts
            for sort in ['hot', 'new']:
                url = f'https://oauth.reddit.com/r/{subreddit}/{sort}'
                params = {'limit': 50}

                response = requests.get(url, headers=headers, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    for child in data.get('data', {}).get('children', []):
                        post = child.get('data', {})
                        post_id = post.get('id')

                        # Skip duplicates
                        if post_id in seen_ids:
                            continue
                        seen_ids.add(post_id)

                        # Check timestamp
                        created = post.get('created_utc', 0)
                        if created < cutoff_timestamp:
                            continue

                        title = post.get('title', '')
                        selftext = post.get('selftext', '')
                        content = (title + ' ' + selftext).lower()

                        # For non-Claude specific subreddits, filter by keywords
                        if subreddit not in ['ClaudeAI']:
                            if not any(kw in content for kw in CLAUDE_KEYWORDS):
                                continue

                        score = post.get('score', 0)
                        num_comments = post.get('num_comments', 0)

                        # Minimum engagement filter
                        if score < 5 and num_comments < 3:
                            continue

                        # Determine category based on flair or content
                        flair = post.get('link_flair_text', '') or ''
                        category = 'community_discussions'

                        if any(kw in content for kw in ['claude code', 'terminal', 'cli', 'vscode']):
                            category = 'claude_code'
                        elif any(kw in flair.lower() for kw in ['tip', 'guide', 'tutorial']):
                            category = 'tutorials_and_tips'
                        elif any(kw in content for kw in ['workflow', 'use case', 'project']):
                            category = 'use_cases'

                        # Build URL
                        permalink = post.get('permalink', '')
                        url = f"https://www.reddit.com{permalink}" if permalink else ''

                        # Get summary (first 300 chars of selftext or title)
                        summary = selftext[:300] + '...' if len(selftext) > 300 else selftext
                        if not summary:
                            summary = f"Discussion in r/{subreddit}"

                        posts.append({
                            'title': title,
                            'url': url,
                            'summary': summary,
                            'published': datetime.fromtimestamp(created).isoformat(),
                            'source': f'Reddit r/{subreddit}',
                            'category': category,
                            'engagement': {
                                'score': score,
                                'comments': num_comments
                            },
                            'flair': flair
                        })

                elif response.status_code == 403:
                    logger.warning(f"Access denied to r/{subreddit}")
                else:
                    logger.warning(f"Reddit API returned {response.status_code} for r/{subreddit}")

        except Exception as e:
            logger.error(f"Error fetching r/{subreddit}: {e}")

    # Sort by engagement
    posts.sort(
        key=lambda x: x['engagement']['score'] + x['engagement']['comments'] * 2,
        reverse=True
    )

    # Limit to top 20
    posts = posts[:20]

    logger.info(f"Collected {len(posts)} Reddit posts")
    return posts


def collect_reddit_tips_and_tutorials():
    """
    Specifically collect tips, tutorials, and guides from Reddit
    """
    tips = []

    token = get_reddit_token()
    if not token:
        return tips

    headers = {
        'Authorization': f'Bearer {token}',
        'User-Agent': 'ClaudeDailyDigest/1.0'
    }

    # Search for tips and tutorials
    search_queries = [
        'flair:tip',
        'flair:guide',
        'title:tips',
        'title:how to',
        'title:tutorial',
        'title:best practices',
    ]

    cutoff_timestamp = (datetime.now() - timedelta(days=14)).timestamp()
    seen_ids = set()

    for query in search_queries:
        try:
            url = 'https://oauth.reddit.com/r/ClaudeAI/search'
            params = {
                'q': query,
                'restrict_sr': 'true',
                'sort': 'relevance',
                'limit': 25,
                't': 'month'  # Last month
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                for child in data.get('data', {}).get('children', []):
                    post = child.get('data', {})
                    post_id = post.get('id')

                    if post_id in seen_ids:
                        continue
                    seen_ids.add(post_id)

                    created = post.get('created_utc', 0)
                    if created < cutoff_timestamp:
                        continue

                    tips.append({
                        'title': post.get('title', ''),
                        'url': f"https://www.reddit.com{post.get('permalink', '')}",
                        'summary': post.get('selftext', '')[:200],
                        'published': datetime.fromtimestamp(created).isoformat(),
                        'source': 'Reddit r/ClaudeAI',
                        'category': 'tutorials_and_tips',
                        'engagement': {
                            'score': post.get('score', 0),
                            'comments': post.get('num_comments', 0)
                        }
                    })

        except Exception as e:
            logger.error(f"Error searching Reddit for '{query}': {e}")

    # Sort and limit
    tips.sort(key=lambda x: x['engagement']['score'], reverse=True)
    return tips[:10]


if __name__ == '__main__':
    # Test the collector
    print("Testing Reddit collector...")
    print("Note: Requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables\n")

    posts = collect_reddit_posts()
    print(f"Found {len(posts)} posts:")
    for p in posts[:5]:
        print(f"  - [{p['category']}] {p['title'][:60]}...")
        print(f"    {p['engagement']['score']} upvotes, {p['engagement']['comments']} comments")
        print()

    tips = collect_reddit_tips_and_tutorials()
    print(f"\nFound {len(tips)} tips/tutorials")
