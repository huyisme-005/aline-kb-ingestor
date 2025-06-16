from backend.scrapers.interviewing_blog import InterviewingBlogScraper
from vcr import VCR

vcr = VCR(cassette_library_dir='backend/tests/fixtures/vcr')

@vcr.use_cassette('backend/tests/fixtures/vcr/blog.yaml')
def test_blog_scraper():
    """
    Verifies that the interviewing.io blog scraper finds links
    and returns valid ContentItem objects.
    """
    scraper = InterviewingBlogScraper()
    links = scraper.discover_links()
    assert links, "Should discover at least one blog link"
    item = scraper.parse_page(links[0])
    assert item.title and item.content
    assert item.content_type == "blog"

