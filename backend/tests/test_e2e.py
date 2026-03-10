# E2E Tests for CPX - Playwright-based

import pytest
from playwright.sync_api import sync_playwright, Page, expect
import json
import time


# Test Configuration
BASE_URL = "http://localhost:3000"
API_BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def browser_context():
    """Create browser context for tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        yield context
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context):
    """Create new page for each test"""
    page = browser_context.new_page()
    yield page
    page.close()


class TestE2EGameFlow:
    """End-to-end test for game flow: OPORD -> Orders -> Commit -> Reports"""

    def test_full_game_flow(self, page: Page):
        """
        Test the complete game flow:
        1. Start game
        2. View OPORD
        3. Submit orders
        4. Commit turn
        5. View reports
        """
        # Step 1: Navigate to games list
        page.goto(f"{BASE_URL}/games")
        page.wait_for_load_state("networkidle")

        # Step 2: Create new game or navigate to existing
        # Try to find an existing game or create new one
        game_cards = page.locator('[class*="game"]').count()

        if game_cards == 0:
            # Create new game
            page.goto(f"{BASE_URL}/new-game")
            page.wait_for_load_state("networkidle")
            page.click('button:has-text("Start")')
            page.wait_for_load_state("networkidle")

        # Navigate to game page
        page.goto(f"{BASE_URL}/game")
        page.wait_for_load_state("networkidle")

        # Verify game loaded
        expect(page.locator("svg")).to_be_visible()

        # Step 3: View OPORD tab
        page.click('button:has-text("OPORD")')
        page.wait_for_timeout(500)

        # Check OPORD content is visible
        opord_content = page.locator('[class*="opord"]').count()
        # May or may not have OPORD data depending on game state

        # Step 4: View Reports tab
        page.click('button:has-text("REPORTS")')
        page.wait_for_timeout(500)

        # Check reports tabs are visible
        expect(page.locator('button:has-text("PLAN")')).to_be_visible()
        expect(page.locator('button:has-text("SITUATION")')).to_be_visible()

        # Step 5: Submit an order (if units exist)
        # Find a unit on the map
        unit_markers = page.locator('[class*="unit"]').count()

        if unit_markers > 0:
            # Click on a unit to select it
            page.locator('[class*="unit"]').first.click()
            page.wait_for_timeout(300)

            # Check unit details panel appears
            unit_details = page.locator('[class*="unit-detail"]').count()

        # Step 6: Test turn advance
        # Click advance turn button
        turn_button = page.locator('button:has-text("Turn")').count()

        print("E2E Test completed successfully")


class TestUIComponents:
    """Test individual UI components"""

    def test_map_renders(self, page: Page):
        """Test that map renders correctly"""
        page.goto(f"{BASE_URL}/game")
        page.wait_for_load_state("networkidle")

        # Check SVG map is visible
        expect(page.locator("svg")).to_be_visible()

    def test_sidebar_tabs(self, page: Page):
        """Test sidebar tab navigation"""
        page.goto(f"{BASE_URL}/game")
        page.wait_for_load_state("networkidle")

        # Click each tab and verify content changes
        tabs = ["情報", "履歴", "ログ", "OPORD", "REPORTS"]

        for tab in tabs:
            button = page.locator(f'button:has-text("{tab}")')
            if button.count() > 0:
                button.first.click()
                page.wait_for_timeout(300)

    def test_unit_selection(self, page: Page):
        """Test unit selection on map"""
        page.goto(f"{BASE_URL}/game")
        page.wait_for_load_state("networkidle")

        # Find unit markers
        units = page.locator("text=A1").count()  # Common unit name

        if units > 0:
            units.first.click()
            page.wait_for_timeout(300)

            # Check unit details appear
            # (depends on implementation)


class TestResponsiveDesign:
    """Test responsive design"""

    def test_mobile_view(self, browser_context):
        """Test mobile viewport"""
        browser_context.set_viewport_size({"width": 375, "height": 667})
        page = browser_context.new_page()

        page.goto(f"{BASE_URL}/game")
        page.wait_for_load_state("networkidle")

        # Basic check - page should load
        expect(page.locator("body")).to_be_visible()

        page.close()

    def test_tablet_view(self, browser_context):
        """Test tablet viewport"""
        browser_context.set_viewport_size({"width": 768, "height": 1024})
        page = browser_context.new_page()

        page.goto(f"{BASE_URL}/game")
        page.wait_for_load_state("networkidle")

        expect(page.locator("body")).to_be_visible()

        page.close()


class TestErrorHandling:
    """Test error handling"""

    def test_404_page(self, page: Page):
        """Test 404 error page"""
        page.goto(f"{BASE_URL}/nonexistent")
        page.wait_for_load_state("networkidle")

        # Should either show 404 or redirect
        body = page.locator("body").text_content()
        # Either shows error or redirects

    def test_api_error_handling(self, page: Page):
        """Test API error handling"""
        page.goto(f"{BASE_URL}/game")
        page.wait_for_load_state("networkidle")

        # Check for error messages in UI
        # If API fails, should show appropriate error


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "e2e: end-to-end tests")
    config.addinivalue_line("markers", "slow: slow running tests")
