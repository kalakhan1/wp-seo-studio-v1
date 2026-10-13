"""Mock WordPress client for testing.

Returns the same typed models as the real WordPressClient so tests can be
swapped between mock and real clients without changing call sites.
"""

from tests.mocks.mock_wordpress.client import MockWordPressClient
from tests.mocks.mock_wordpress.routes import MockWordPressRoutes

__all__ = ["MockWordPressClient", "MockWordPressRoutes"]