#!/usr/bin/env python3
"""
Email sending script for Claude Daily Digest
Renders HTML template and sends via Gmail SMTP
"""

import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime
from jinja2 import Template
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_digest_data():
    """Load the daily digest data"""
    project_root = Path(__file__).parent.parent
    data_file = project_root / 'data' / 'daily_digest.json'

    if not data_file.exists():
        logger.error(f"Digest data file not found: {data_file}")
        sys.exit(1)

    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def render_email_html(digest_data):
    """Render email HTML from template"""
    project_root = Path(__file__).parent.parent
    template_file = project_root / 'templates' / 'email_template.html'

    if not template_file.exists():
        logger.error(f"Template file not found: {template_file}")
        sys.exit(1)

    with open(template_file, 'r', encoding='utf-8') as f:
        template_content = f.read()

    template = Template(template_content)

    # Prepare template data
    template_data = {
        'date': datetime.now().strftime('%Y年%m月%d日'),
        'official_updates': digest_data.get('official_updates', []),
        'github_projects': digest_data.get('github_projects', []),
        'blog_posts': digest_data.get('blog_posts', []),
        'total_items': digest_data.get('total_items', 0),
    }

    return template.render(**template_data)


def send_email(html_content, digest_data):
    """Send email via Gmail SMTP"""

    # Get credentials from environment
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = os.environ.get('RECIPIENT_EMAIL')

    if not all([gmail_user, gmail_password, recipient]):
        logger.error("Missing email credentials in environment variables")
        logger.error("Required: GMAIL_USER, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL")
        sys.exit(1)

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"📰 Claude Daily Digest - {datetime.now().strftime('%Y/%m/%d')}"
    msg['From'] = gmail_user
    msg['To'] = recipient

    # Add HTML content
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(html_part)

    # Send email
    try:
        logger.info("Connecting to Gmail SMTP server...")
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)

        logger.info("Logging in...")
        server.login(gmail_user, gmail_password)

        logger.info(f"Sending email to {recipient}...")
        server.sendmail(gmail_user, recipient, msg.as_string())

        server.quit()

        logger.info("✓ Email sent successfully!")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Authentication failed. Please check your Gmail credentials.")
        logger.error("Make sure you're using an App Password, not your regular password.")
        logger.error("Visit: https://myaccount.google.com/apppasswords")
        return False

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def save_html_preview(html_content):
    """Save HTML preview for testing"""
    project_root = Path(__file__).parent.parent
    preview_file = project_root / 'data' / 'email_preview.html'

    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"HTML preview saved to: {preview_file}")


def main():
    """Main email sending function"""
    logger.info("=" * 60)
    logger.info("Starting email digest generation")
    logger.info("=" * 60)

    # Load digest data
    logger.info("\n1. Loading digest data...")
    digest_data = load_digest_data()

    total_items = digest_data.get('total_items', 0)
    logger.info(f"   Total items: {total_items}")

    # Check if there's content to send
    if total_items == 0:
        logger.warning("\n⚠ No new content to send today")
        logger.info("Skipping email send")
        sys.exit(0)

    # Render HTML
    logger.info("\n2. Rendering email HTML...")
    html_content = render_email_html(digest_data)

    # Save preview (useful for debugging)
    save_html_preview(html_content)

    # Send email
    logger.info("\n3. Sending email...")
    success = send_email(html_content, digest_data)

    if success:
        logger.info("\n" + "=" * 60)
        logger.info("Email sent successfully!")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("\n" + "=" * 60)
        logger.error("Failed to send email")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
