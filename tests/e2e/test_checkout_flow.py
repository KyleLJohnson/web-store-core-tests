import pytest
from playwright.sync_api import Page, expect


def test_browse_msn(page: Page):
    """Test browsing to msn.com."""
    page.goto("https://www.msn.com")
    
    expect(page).to_have_title_containing("MSN")
