"""
Collector for GitHub trending projects related to Claude
"""

import os
from github import Github
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collect_github_projects():
    """
    Collect Claude-related projects from GitHub
    Returns a list of projects
    """
    projects = []

    # Get GitHub token from environment
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        logger.warning("No GITHUB_TOKEN found, skipping GitHub collection")
        return projects

    try:
        g = Github(github_token)

        # Search for Claude-related repositories
        # Balance between Claude API and Claude Code (1:1 ratio)
        search_queries = [
            # Claude API related
            'claude anthropic',
            'claude api',
            'anthropic sdk',
            # Claude Code related
            'claude-code',
            'claude code cli',
            'mcp server anthropic',
            'model context protocol',
        ]

        seen_repos = set()

        for query in search_queries:
            logger.info(f"Searching GitHub for: {query}")

            # Search repositories
            repos = g.search_repositories(
                query=query,
                sort='stars',
                order='desc'
            )

            # Get top 10 results
            for repo in repos[:10]:
                # Avoid duplicates
                if repo.full_name in seen_repos:
                    continue

                seen_repos.add(repo.full_name)

                # Check if it's recent or actively maintained
                is_recent = (datetime.now() - repo.updated_at) < timedelta(days=90)

                if repo.stargazers_count >= 10 or is_recent:
                    projects.append({
                        'title': repo.full_name,
                        'url': repo.html_url,
                        'description': repo.description or 'No description provided',
                        'stars': repo.stargazers_count,
                        'language': repo.language,
                        'updated': repo.updated_at.isoformat(),
                        'source': 'GitHub',
                        'category': 'github_projects',
                        'owner_avatar': repo.owner.avatar_url if repo.owner else None
                    })

        # Sort by stars
        projects.sort(key=lambda x: x['stars'], reverse=True)

        # Limit to top 15
        projects = projects[:15]

        logger.info(f"Collected {len(projects)} GitHub projects")

    except Exception as e:
        logger.error(f"Error collecting GitHub projects: {e}")

    return projects


def collect_recent_releases():
    """
    Collect recent releases from important Claude-related repos
    """
    releases = []

    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        return releases

    try:
        g = Github(github_token)

        # Important repos to monitor
        # Balance between Claude API and Claude Code
        important_repos = [
            # Claude API / SDK
            'anthropics/anthropic-sdk-python',
            'anthropics/anthropic-sdk-typescript',
            'anthropics/anthropic-cookbook',
            'anthropics/courses',
            # Claude Code related
            'anthropics/claude-code',
            'modelcontextprotocol/servers',
            'modelcontextprotocol/typescript-sdk',
            'modelcontextprotocol/python-sdk',
        ]

        for repo_name in important_repos:
            try:
                repo = g.get_repo(repo_name)
                latest_releases = repo.get_releases()[:3]  # Get 3 most recent

                for release in latest_releases:
                    # Only include releases from last 30 days
                    if (datetime.now() - release.created_at) < timedelta(days=30):
                        releases.append({
                            'title': f"{repo_name}: {release.title}",
                            'url': release.html_url,
                            'description': release.body[:200] if release.body else 'No description',
                            'published': release.created_at.isoformat(),
                            'source': 'GitHub Releases',
                            'category': 'github_projects'
                        })
            except Exception as e:
                logger.warning(f"Could not fetch releases for {repo_name}: {e}")

    except Exception as e:
        logger.error(f"Error collecting releases: {e}")

    return releases


if __name__ == '__main__':
    # Test the collector
    projects = collect_github_projects()
    print(f"Found {len(projects)} projects:")
    for project in projects[:5]:
        print(f"  - {project['title']} ({project['stars']} stars)")

    releases = collect_recent_releases()
    print(f"\nFound {len(releases)} recent releases")
