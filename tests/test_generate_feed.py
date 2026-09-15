import datetime as dt
import unittest
from generate_feed import newest

class FeedTests(unittest.TestCase):
    def test_selects_newest_playable_item(self):
        xml=b'''<rss><channel><item><title>old</title><pubDate>Mon, 14 Sep 2026 06:00:00 GMT</pubDate><enclosure url="https://e/x.mp3" type="audio/mpeg" length="10"/></item><item><title>new</title><pubDate>Tue, 15 Sep 2026 06:00:00 GMT</pubDate><enclosure url="https://e/y.mp3" type="audio/mpeg" length="20"/></item></channel></rss>'''
        published,item,audio,enclosure=newest(xml)
        self.assertEqual(item.find("title").text, "new")
        self.assertEqual(audio, "https://e/y.mp3")
        self.assertEqual(published, dt.datetime(2026,9,15,6,tzinfo=dt.timezone.utc))
