#!/usr/bin/env python3
"""
Summary Generator for Claude Daily Digest
- Extracts article content using trafilatura
- Creates summaries by intelligent text extraction (no API needed)
"""

import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import requests
import trafilatura

logger = logging.getLogger(__name__)

# Configuration
FETCH_TIMEOUT = 10
MAX_CONTENT_LENGTH = 8000
TARGET_SUMMARY_LENGTH = 500  # Target characters for summary


class SummaryGenerator:
    """Generate article summaries by extracting content"""

    def __init__(self):
        pass

    def extract_content(self, url: str, source_type: str = '') -> Optional[str]:
        """
        Extract article content from URL
        Uses trafilatura for general web content
        """
        try:
            # Special handling for different source types
            if 'github.com' in url:
                return self._extract_github_readme(url)

            # Use trafilatura for general web content
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=False,
                    no_fallback=False
                )
                if text:
                    return text[:MAX_CONTENT_LENGTH]

            return None

        except Exception as e:
            logger.warning(f"Content extraction failed for {url}: {e}")
            return None

    def _extract_github_readme(self, url: str) -> Optional[str]:
        """Extract README content from GitHub repository"""
        try:
            # Parse GitHub URL: github.com/owner/repo
            match = re.match(r'https?://github\.com/([^/]+)/([^/]+)', url)
            if not match:
                return None

            owner, repo = match.groups()
            repo = repo.split('?')[0].split('#')[0]  # Clean up URL params

            # Try to fetch README via API
            api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            headers = {'Accept': 'application/vnd.github.raw'}

            response = requests.get(api_url, headers=headers, timeout=FETCH_TIMEOUT)
            if response.status_code == 200:
                return response.text[:MAX_CONTENT_LENGTH]

            return None

        except Exception as e:
            logger.warning(f"GitHub README extraction failed: {e}")
            return None

    def create_summary(self, content: str, target_length: int = TARGET_SUMMARY_LENGTH) -> str:
        """
        Create summary by intelligent text extraction
        Extracts the most informative beginning of the article
        Cuts at sentence boundaries for clean reading
        """
        if not content:
            return ""

        # Clean up the content
        content = content.strip()

        # Remove common noise at the beginning
        lines = content.split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            # Skip very short lines (likely headers/nav)
            if len(line) < 20:
                continue
            # Skip lines that look like metadata
            if line.startswith(('Share', 'Tweet', 'Follow', 'Subscribe', 'Sign up')):
                continue
            clean_lines.append(line)

        content = ' '.join(clean_lines)

        if len(content) <= target_length:
            return content

        # Try to find a good cut point near target length
        search_start = max(0, target_length - 100)
        search_end = min(len(content), target_length + 100)
        search_text = content[search_start:search_end]

        # Look for sentence endings (Chinese period first, then English)
        cut_offset = search_text.rfind('。')
        if cut_offset == -1:
            cut_offset = search_text.rfind('. ')
        if cut_offset == -1:
            cut_offset = search_text.rfind('! ')
        if cut_offset == -1:
            cut_offset = search_text.rfind('? ')
        if cut_offset == -1:
            # Just cut at target length
            cut_offset = target_length - search_start

        cut_point = search_start + cut_offset + 1
        summary = content[:cut_point].strip()

        # Add ellipsis if we cut the content
        if len(content) > len(summary):
            summary += '...'

        return summary


def enrich_item_with_summary(item: dict, generator: SummaryGenerator) -> dict:
    """
    Enrich a single item with summary
    Extracts article content and creates a ~500 char summary
    """
    # Skip if already has a good summary (>200 chars)
    existing = item.get('summary', '')
    if existing and len(existing) > 200:
        logger.debug(f"Skipping, already has summary: {item.get('title', '')[:30]}")
        return item

    url = item.get('url', '')
    title = item.get('title', '')
    source = item.get('source', '')

    if not url:
        return item

    try:
        # Extract content from the article
        content = generator.extract_content(url, source)

        if not content:
            logger.warning(f"No content extracted from: {url}")
            return item

        # Create summary by intelligent extraction
        summary = generator.create_summary(content)

        if summary and len(summary) > len(existing):
            item['summary'] = summary
            logger.info(f"Created summary for: {title[:40]}...")

    except requests.Timeout:
        logger.warning(f"Request timeout: {url}")
    except Exception as e:
        logger.error(f"Summary enrichment failed for {url}: {e}")

    return item


def enrich_items_with_summaries(items: list, max_workers: int = 5) -> list:
    """
    Enrich multiple items with summaries in parallel
    No API needed - extracts content and creates summaries locally

    Args:
        items: List of content items
        max_workers: Number of parallel workers

    Returns:
        List of items with summaries added
    """
    if not items:
        return items

    generator = SummaryGenerator()

    logger.info(f"Extracting content and creating summaries for {len(items)} items...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(enrich_item_with_summary, item, generator): i
            for i, item in enumerate(items)
        }

        for future in as_completed(futures):
            idx = futures[future]
            try:
                items[idx] = future.result()
            except Exception as e:
                logger.error(f"Summary error for item {idx}: {e}")

    # Count successful summaries
    with_summary = sum(1 for item in items if item.get('summary') and len(item.get('summary', '')) > 100)
    logger.info(f"Summary extraction complete: {with_summary}/{len(items)} items have summaries")

    return items


if __name__ == '__main__':
    # Test the module
    logging.basicConfig(level=logging.INFO)

    test_items = [
        {
            'title': 'Model Context Protocol',
            'url': 'https://www.anthropic.com/news/model-context-protocol',
            'summary': '',
            'source': 'Anthropic News'
        }
    ]

    result = enrich_items_with_summaries(test_items)
    print(f"\nResult summary ({len(result[0].get('summary', ''))} chars):")
    print(result[0].get('summary', 'No summary generated'))
