"""
Data collectors for Claude Daily Digest
"""

from .anthropic_docs import collect_anthropic_updates
from .github_trends import collect_github_projects, collect_recent_releases
from .rss_aggregator import collect_blog_posts
from .hackernews_collector import collect_hackernews_discussions, collect_hn_claude_code_posts
from .reddit_collector import collect_reddit_posts, collect_reddit_tips_and_tutorials
from .devto_collector import collect_devto_articles

__all__ = [
    # Official sources
    'collect_anthropic_updates',
    # GitHub
    'collect_github_projects',
    'collect_recent_releases',
    # Blogs and RSS
    'collect_blog_posts',
    # Community discussions
    'collect_hackernews_discussions',
    'collect_hn_claude_code_posts',
    'collect_reddit_posts',
    'collect_reddit_tips_and_tutorials',
    # Developer tutorials
    'collect_devto_articles',
]
