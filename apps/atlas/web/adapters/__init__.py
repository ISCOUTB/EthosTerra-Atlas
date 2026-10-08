from apps.atlas.web.adapters.base import BaseDiscoveryAdapter
from apps.atlas.web.adapters.socrata_adapter import SocrataCatalogAdapter
from apps.atlas.web.adapters.dcat_adapter import DcatAdapter
from apps.atlas.web.adapters.sitemap_adapter import SitemapAdapter
from apps.atlas.web.adapters.feed_adapter import FeedAdapter
from apps.atlas.web.adapters.native_search_adapter import NativeSearchAdapter
from apps.atlas.web.adapters.focused_crawler import FocusedHtmlCrawler
from apps.atlas.web.adapters.playwright_adapter import PlaywrightFallbackAdapter

__all__ = [
    "BaseDiscoveryAdapter",
    "SocrataCatalogAdapter",
    "DcatAdapter",
    "SitemapAdapter",
    "FeedAdapter",
    "NativeSearchAdapter",
    "FocusedHtmlCrawler",
    "PlaywrightFallbackAdapter",
]
