import pytest
import re
from playwright.sync_api import Page, expect


def test_guest_checkout(page: Page):
    """Test browsing to msn.com."""
    page.goto("https://www.msn.com")
    
    expect(page).to_have_title(re.compile("MSN"))
