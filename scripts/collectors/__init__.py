"""
Data collectors for Claude Daily Digest
"""

from .anthropic_docs import collect_anthropic_updates
from .github_trends import collect_github_projects
from .rss_aggregator import collect_blog_posts

__all__ = [
    'collect_anthropic_updates',
    'collect_github_projects',
    'collect_blog_posts',
]
