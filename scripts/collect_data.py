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
    collect_anthropic_updates,
    collect_github_projects,
    collect_blog_posts
)

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
    """
    score = 0

    title = item.get('title', '').lower()
    content = item.get('summary', '') + item.get('description', '')
    content = content.lower()

    # High value keywords
    high_value = [
        'claude', 'anthropic', 'api', 'update', 'release',
        'tutorial', 'guide', 'best practices', 'how to',
        'announcement', 'feature', 'new'
    ]

    # Medium value keywords
    medium_value = [
        'tips', 'tricks', 'example', 'use case', 'integration',
        'review', 'comparison', 'analysis'
    ]

    # Count keyword matches
    for keyword in high_value:
        if keyword in title:
            score += 15
        if keyword in content:
            score += 5

    for keyword in medium_value:
        if keyword in title:
            score += 10
        if keyword in content:
            score += 3

    # Bonus for official sources
    if item.get('source') in ['Anthropic News', 'Anthropic Docs', 'GitHub Releases']:
        score += 30

    # Bonus for GitHub stars
    if 'stars' in item and item['stars'] > 100:
        score += 20
    elif 'stars' in item and item['stars'] > 50:
        score += 10

    # Length bonus (substance)
    if len(content) > 500:
        score += 10

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
    logger.info("\n1. Collecting Anthropic updates...")
    anthropic_updates = collect_anthropic_updates()

    logger.info("\n2. Collecting GitHub projects...")
    github_projects = collect_github_projects()

    logger.info("\n3. Collecting blog posts...")
    blog_posts = collect_blog_posts()

    # Combine all content
    all_content = anthropic_updates + github_projects + blog_posts

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

    # Organize by category
    digest_data = {
        'generated_at': datetime.now().isoformat(),
        'total_items': len(quality_content),
        'official_updates': [
            item for item in quality_content
            if item.get('category') == 'official_updates'
        ],
        'github_projects': [
            item for item in quality_content
            if item.get('category') == 'github_projects'
        ],
        'blog_posts': [
            item for item in quality_content
            if item.get('category') == 'blog_posts'
        ],
        'all_items': quality_content[:30]  # Limit to top 30
    }

    # Save digest data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(digest_data, f, indent=2, ensure_ascii=False)

    logger.info(f"\nDigest saved to {output_path}")
    logger.info(f"  - Official updates: {len(digest_data['official_updates'])}")
    logger.info(f"  - GitHub projects: {len(digest_data['github_projects'])}")
    logger.info(f"  - Blog posts: {len(digest_data['blog_posts'])}")

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
