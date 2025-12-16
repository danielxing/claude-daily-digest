"""
Utility for fetching images/thumbnails for content items
Uses Open Graph images from article pages
"""

import re
import requests
from urllib.parse import urlparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default timeout for image fetching
FETCH_TIMEOUT = 5

# Known site logos as fallback
SITE_LOGOS = {
    'github.com': 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png',
    'news.ycombinator.com': 'https://news.ycombinator.com/y18.svg',
    'reddit.com': 'https://www.redditstatic.com/desktop2x/img/favicon/android-icon-192x192.png',
    'dev.to': 'https://dev-to-uploads.s3.amazonaws.com/uploads/logos/resized_logo_UQww2soKuUsjaOGNB38o.png',
    'anthropic.com': 'https://www.anthropic.com/images/icons/apple-touch-icon.png',
    'docs.anthropic.com': 'https://www.anthropic.com/images/icons/apple-touch-icon.png',
    'medium.com': 'https://cdn-images-1.medium.com/fit/c/152/152/1*sHhtYhaCe2Uc3IU0IgKwIQ.png',
}


def get_domain(url):
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    except:
        return None


def fetch_og_image(url, timeout=FETCH_TIMEOUT):
    """
    Fetch Open Graph image from URL
    Returns image URL or None
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)

        if response.status_code == 200:
            content = response.text[:15000]  # Check first 15KB

            # Pattern 1: og:image with content after property
            og_patterns = [
                r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\'](https?://[^"\']+)["\']',
                r'<meta[^>]*content=["\'](https?://[^"\']+)["\'][^>]*property=["\']og:image["\']',
                r'<meta[^>]*name=["\']twitter:image["\'][^>]*content=["\'](https?://[^"\']+)["\']',
                r'<meta[^>]*content=["\'](https?://[^"\']+)["\'][^>]*name=["\']twitter:image["\']',
                r'<meta[^>]*name=["\']twitter:image:src["\'][^>]*content=["\'](https?://[^"\']+)["\']',
            ]

            for pattern in og_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    image_url = match.group(1)
                    # Filter out tracking pixels or tiny images
                    if 'pixel' not in image_url.lower() and '1x1' not in image_url:
                        return image_url

    except requests.Timeout:
        logger.debug(f"Timeout fetching OG image from {url}")
    except Exception as e:
        logger.debug(f"Could not fetch OG image from {url}: {e}")

    return None


def get_fallback_image(url):
    """Get fallback image based on domain"""
    domain = get_domain(url)
    if not domain:
        return None

    # Check known sites
    for known_domain, image_url in SITE_LOGOS.items():
        if known_domain in domain:
            return image_url

    # Google favicon API as last resort
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"


def get_image_for_item(item, fetch_og=True):
    """
    Get an image URL for a content item

    Args:
        item: dict with 'url' key
        fetch_og: whether to fetch OG image from the page

    Returns:
        Updated item with 'image_url' key
    """
    # Skip if already has image
    if item.get('image_url') or item.get('owner_avatar'):
        return item

    url = item.get('url', '')
    image_url = None

    # Try OG image first (best quality)
    if fetch_og and url:
        image_url = fetch_og_image(url)
        if image_url:
            logger.debug(f"Found OG image for {url}: {image_url}")

    # Fall back to site logo/favicon
    if not image_url:
        image_url = get_fallback_image(url)

    if image_url:
        item['image_url'] = image_url

    return item


def enrich_items_with_images(items, fetch_og=True, max_workers=5):
    """
    Add images to a list of content items in parallel

    Args:
        items: list of content items
        fetch_og: whether to fetch OG images
        max_workers: number of parallel threads
    """
    if not fetch_og:
        # Fast path - just add fallback images
        for item in items:
            if not item.get('image_url') and not item.get('owner_avatar'):
                item['image_url'] = get_fallback_image(item.get('url', ''))
        return items

    # Parallel fetch for OG images
    def fetch_image(item):
        return get_image_for_item(item, fetch_og=True)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_image, item): item for item in items}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.debug(f"Error fetching image: {e}")

    return items


if __name__ == '__main__':
    # Test
    test_items = [
        {'url': 'https://github.com/anthropics/claude-code', 'title': 'Claude Code'},
        {'url': 'https://news.ycombinator.com/item?id=12345', 'title': 'HN Post'},
        {'url': 'https://dev.to/some-article', 'title': 'Dev.to Article'},
        {'url': 'https://www.anthropic.com/news/some-post', 'title': 'Anthropic News'},
    ]

    print("Testing OG image fetching...")
    for item in test_items:
        get_image_for_item(item, fetch_og=True)
        print(f"  {item['title']}: {item.get('image_url', 'No image')}")
