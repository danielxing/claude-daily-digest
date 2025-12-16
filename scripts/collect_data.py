#!/usr/bin/env python3
"""
Main data collection script for Claude Daily Digest
Collects data from all sources and saves to database
"""

import sys
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from tinydb import TinyDB, Query
import logging

# Add collectors to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'collectors'))

from collectors import (
    # Official sources
    collect_anthropic_updates,
    # GitHub
    collect_github_projects,
    collect_recent_releases,
    # Blogs
    collect_blog_posts,
    # Community discussions
    collect_hackernews_discussions,
    collect_hn_claude_code_posts,
    collect_reddit_posts,
    collect_reddit_tips_and_tutorials,
    # Developer tutorials
    collect_devto_articles,
)
from collectors.image_fetcher import enrich_items_with_images, get_image_for_item
from collectors.summary_generator import enrich_items_with_summaries

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentDatabase:
    """Simple database for tracking seen content"""

    def __init__(self, db_path):
        self.db = TinyDB(db_path)
        self.Content = Query()

    def get_fingerprint(self, url, title):
        """Generate unique fingerprint for content"""
        return hashlib.md5(f"{url}{title}".encode()).hexdigest()

    def is_duplicate(self, url, title):
        """Check if content has been seen before"""
        fingerprint = self.get_fingerprint(url, title)
        return len(self.db.search(self.Content.fingerprint == fingerprint)) > 0

    def add_content(self, item):
        """Add content to database"""
        fingerprint = self.get_fingerprint(item['url'], item['title'])
        self.db.insert({
            'fingerprint': fingerprint,
            'url': item['url'],
            'title': item['title'],
            'timestamp': datetime.now().isoformat(),
            'category': item.get('category', 'unknown')
        })

    def cleanup_old_entries(self, days=30):
        """Remove entries older than specified days"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)

        def is_old(doc):
            doc_date = datetime.fromisoformat(doc['timestamp'])
            return doc_date < cutoff

        self.db.remove(is_old)


def calculate_quality_score(item):
    """
    Calculate quality score for content item
    Higher score = better quality
    Prioritizes practical content (tutorials, tips, use cases)
    """
    score = 0

    title = item.get('title', '').lower()
    content = item.get('summary', '') + item.get('description', '')
    content = content.lower()

    # High value - Practical content (tutorials, tips, use cases)
    practical_keywords = [
        'tutorial', 'guide', 'how to', 'step by step',
        'tips', 'tricks', 'best practices', 'workflow',
        'use case', 'example', 'template', 'prompt'
    ]

    # High value - Claude Code specific
    claude_code_keywords = [
        'claude code', 'claude-code', 'mcp', 'model context protocol',
        'terminal', 'cli', 'vscode', 'agentic', 'agent',
        'coding assistant', 'code generation'
    ]

    # High value - Official updates
    official_keywords = [
        'claude', 'anthropic', 'api', 'update', 'release',
        'announcement', 'feature', 'new', 'sonnet', 'opus', 'haiku'
    ]

    # Medium value - General tech content
    medium_keywords = [
        'integration', 'review', 'comparison', 'analysis',
        'project', 'built with', 'created'
    ]

    # Score practical content highest (user priority)
    for keyword in practical_keywords:
        if keyword in title:
            score += 20
        if keyword in content:
            score += 8

    # Score Claude Code content high (1:1 ratio with Claude API)
    for keyword in claude_code_keywords:
        if keyword in title:
            score += 18
        if keyword in content:
            score += 7

    # Score official keywords
    for keyword in official_keywords:
        if keyword in title:
            score += 15
        if keyword in content:
            score += 5

    # Medium value keywords
    for keyword in medium_keywords:
        if keyword in title:
            score += 10
        if keyword in content:
            score += 3

    # Bonus for official sources
    if item.get('source') in ['Anthropic News', 'Anthropic Docs', 'GitHub Releases']:
        score += 30

    # Bonus for high engagement community content
    engagement = item.get('engagement', {})
    if engagement:
        points = engagement.get('points', 0) or engagement.get('score', 0) or engagement.get('reactions', 0)
        comments = engagement.get('comments', 0)

        if points > 100:
            score += 25
        elif points > 50:
            score += 15
        elif points > 20:
            score += 10

        if comments > 50:
            score += 15
        elif comments > 20:
            score += 10

    # Bonus for GitHub stars
    if 'stars' in item:
        if item['stars'] > 500:
            score += 25
        elif item['stars'] > 100:
            score += 20
        elif item['stars'] > 50:
            score += 10

    # Length bonus (substance)
    if len(content) > 500:
        score += 10
    elif len(content) > 200:
        score += 5

    return score


def filter_and_rank_content(items, min_score=20):
    """Filter content by quality score and rank"""
    scored_items = []

    for item in items:
        score = calculate_quality_score(item)
        if score >= min_score:
            item['quality_score'] = score
            scored_items.append(item)

    # Sort by score
    scored_items.sort(key=lambda x: x['quality_score'], reverse=True)

    return scored_items


def main():
    """Main collection function"""
    logger.info("=" * 60)
    logger.info("Starting Claude Daily Digest data collection")
    logger.info("=" * 60)

    # Setup paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)

    db_path = data_dir / 'content_db.json'
    output_path = data_dir / 'daily_digest.json'

    # Initialize database
    db = ContentDatabase(db_path)

    # Collect data from all sources
    logger.info("\n1. Collecting Anthropic official updates...")
    anthropic_updates = collect_anthropic_updates()

    logger.info("\n2. Collecting GitHub projects...")
    github_projects = collect_github_projects()

    logger.info("\n3. Collecting GitHub releases...")
    github_releases = collect_recent_releases()

    logger.info("\n4. Collecting blog posts (RSS)...")
    blog_posts = collect_blog_posts()

    logger.info("\n5. Collecting Hacker News discussions...")
    hn_discussions = collect_hackernews_discussions()
    hn_claude_code = collect_hn_claude_code_posts()

    logger.info("\n6. Collecting Reddit posts...")
    reddit_posts = collect_reddit_posts()
    reddit_tips = collect_reddit_tips_and_tutorials()

    logger.info("\n7. Collecting Dev.to articles...")
    devto_articles = collect_devto_articles()

    # Combine all content
    all_content = (
        anthropic_updates +
        github_projects +
        github_releases +
        blog_posts +
        hn_discussions +
        hn_claude_code +
        reddit_posts +
        reddit_tips +
        devto_articles
    )

    logger.info(f"\nTotal items collected: {len(all_content)}")

    # Filter duplicates
    new_content = []
    for item in all_content:
        if not db.is_duplicate(item['url'], item['title']):
            new_content.append(item)
            db.add_content(item)
        else:
            logger.debug(f"Skipping duplicate: {item['title']}")

    logger.info(f"New items (after deduplication): {len(new_content)}")

    # Filter and rank by quality
    quality_content = filter_and_rank_content(new_content, min_score=15)

    logger.info(f"Quality items (score >= 15): {len(quality_content)}")

    # Enrich with images (fetch OG images for better quality)
    logger.info("\n8. Adding images to content items...")
    quality_content = enrich_items_with_images(quality_content, fetch_og=True, max_workers=8)
    logger.info("   Images added (with OG image fetching)")

    # Enrich with summaries (extract content and generate Chinese summaries)
    logger.info("\n9. Generating article summaries...")
    quality_content = enrich_items_with_summaries(quality_content, max_workers=3)
    logger.info("   Summaries generated")

    # Select featured item (highest quality score)
    featured_item = quality_content[0] if quality_content else None

    # Get remaining items (excluding featured), limited to 9 for total of 10
    remaining_items = quality_content[1:10] if len(quality_content) > 1 else []

    # Organize by category (new structure with practical content focus)
    digest_data = {
        'generated_at': datetime.now().isoformat(),
        'total_items': min(len(quality_content), 10),  # Limit to 10 items

        # Featured item (Editor's Pick)
        'featured_item': featured_item,

        # All remaining items (for the list view)
        'items': remaining_items,

        # Category breakdown (for reference)
        'tutorials_and_tips': [
            item for item in remaining_items
            if item.get('category') == 'tutorials_and_tips'
        ],
        'use_cases': [
            item for item in remaining_items
            if item.get('category') == 'use_cases'
        ],
        'claude_code': [
            item for item in remaining_items
            if item.get('category') == 'claude_code'
        ],
        'official_updates': [
            item for item in remaining_items
            if item.get('category') == 'official_updates'
        ],
        'community_discussions': [
            item for item in remaining_items
            if item.get('category') == 'community_discussions'
        ],
        'github_projects': [
            item for item in remaining_items
            if item.get('category') == 'github_projects'
        ],
        'blog_posts': [
            item for item in remaining_items
            if item.get('category') == 'blog_posts'
        ],
    }

    # Save digest data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(digest_data, f, indent=2, ensure_ascii=False)

    logger.info(f"\nDigest saved to {output_path}")
    logger.info(f"  - Total items: {digest_data['total_items']}")
    logger.info(f"  - Featured: {featured_item['title'][:50] if featured_item else 'None'}...")
    logger.info(f"  - List items: {len(digest_data['items'])}")

    # Cleanup old database entries
    db.cleanup_old_entries(days=30)

    logger.info("\n" + "=" * 60)
    logger.info("Data collection complete!")
    logger.info("=" * 60)

    return digest_data


if __name__ == '__main__':
    try:
        digest_data = main()

        # Exit with error if no new content
        if digest_data['total_items'] == 0:
            logger.warning("No new content found today")
            sys.exit(1)

        sys.exit(0)

    except Exception as e:
        logger.error(f"Error during collection: {e}", exc_info=True)
        sys.exit(1)
