import asyncio
import urllib.parse
from fastapi import Request

from backend.app.config import settings
from backend.app.enums import FileTypeEnum, RatingEnum, TagCategoryEnum
from backend.app.models import Album, Media, Tag, blombooru_album_hierarchy, blombooru_album_media, blombooru_media_tags
from backend.app.redis_client import redis_cache
from backend.app.routes.albums import get_album_contents, get_albums
from backend.app.routes.media import get_adjacent_media, get_media_list
from backend.app.routes.search import get_random_media, search_media
from backend.app.routes.tags import search_related_tags
from backend.app.schemas import SettingsUpdate
from tests.backup_test_base import BackupTestBase

def make_dummy_request(path: str = "/api/test", query_params: dict = None) -> Request:
    query_str = urllib.parse.urlencode(query_params or {}).encode()
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
        "query_string": query_str,
    }
    return Request(scope)

class TestRatingFilterMode(BackupTestBase):
    def setUp(self):
        super().setUp()
        self.old_redis_enabled = redis_cache._enabled
        redis_cache._enabled = False

        # Seed test media items with safe, questionable, and explicit ratings
        self.media_safe = Media(
            id=1,
            filename="safe_1.jpg",
            path="original/safe_1.jpg",
            hash="hash_safe_1",
            file_type=FileTypeEnum.image,
            rating=RatingEnum.safe,
            file_size=1024,
        )
        self.media_quest = Media(
            id=2,
            filename="quest_1.jpg",
            path="original/quest_1.jpg",
            hash="hash_quest_1",
            file_type=FileTypeEnum.image,
            rating=RatingEnum.questionable,
            file_size=2048,
        )
        self.media_expl = Media(
            id=3,
            filename="expl_1.jpg",
            path="original/expl_1.jpg",
            hash="hash_expl_1",
            file_type=FileTypeEnum.image,
            rating=RatingEnum.explicit,
            file_size=4096,
        )
        self.db.add_all([self.media_safe, self.media_quest, self.media_expl])

        self.tag_cat = Tag(id=1, name="cat", category=TagCategoryEnum.character, post_count=3)
        self.db.add(self.tag_cat)
        self.db.commit()

        # Link tag to all media
        self.db.execute(blombooru_media_tags.insert().values([
            {"media_id": 1, "tag_id": 1},
            {"media_id": 2, "tag_id": 1},
            {"media_id": 3, "tag_id": 1},
        ]))
        self.db.commit()

    def tearDown(self):
        redis_cache._enabled = self.old_redis_enabled
        super().tearDown()

    def test_search_media_rating_modes(self):
        req = make_dummy_request()

        def get_ids(res):
            return [item["id"] if isinstance(item, dict) else item.id for item in res["items"]]

        # 1. Default (omitted rating_mode) -> inclusive
        res_safe = asyncio.run(search_media(request=req, rating="safe", db=self.db))
        self.assertEqual(get_ids(res_safe), [1])

        res_quest = asyncio.run(search_media(request=req, rating="questionable", db=self.db))
        self.assertCountEqual(get_ids(res_quest), [1, 2])

        res_expl = asyncio.run(search_media(request=req, rating="explicit", db=self.db))
        self.assertCountEqual(get_ids(res_expl), [1, 2, 3])

        # 2. Explicit rating_mode="inclusive"
        res_quest_inc = asyncio.run(search_media(request=req, rating="questionable", rating_mode="inclusive", db=self.db))
        self.assertCountEqual(get_ids(res_quest_inc), [1, 2])

        # 3. Explicit rating_mode="exact"
        res_exact_safe = asyncio.run(search_media(request=req, rating="safe", rating_mode="exact", db=self.db))
        self.assertEqual(get_ids(res_exact_safe), [1])

        res_exact_quest = asyncio.run(search_media(request=req, rating="questionable", rating_mode="exact", db=self.db))
        self.assertEqual(get_ids(res_exact_quest), [2])

        res_exact_expl = asyncio.run(search_media(request=req, rating="explicit", rating_mode="exact", db=self.db))
        self.assertEqual(get_ids(res_exact_expl), [3])

    def test_get_media_list_rating_modes(self):
        req = make_dummy_request()

        def get_ids(res):
            return [item["id"] if isinstance(item, dict) else item.id for item in res["items"]]

        # 1. Default (omitted rating_mode) -> inclusive
        res_safe = asyncio.run(get_media_list(request=req, rating="safe", db=self.db))
        self.assertEqual(get_ids(res_safe), [1])

        res_quest = asyncio.run(get_media_list(request=req, rating="questionable", db=self.db))
        self.assertCountEqual(get_ids(res_quest), [1, 2])

        res_expl = asyncio.run(get_media_list(request=req, rating="explicit", db=self.db))
        self.assertCountEqual(get_ids(res_expl), [1, 2, 3])

        # 2. Exact mode
        res_exact_safe = asyncio.run(get_media_list(request=req, rating="safe", rating_mode="exact", db=self.db))
        self.assertEqual(get_ids(res_exact_safe), [1])

        res_exact_quest = asyncio.run(get_media_list(request=req, rating="questionable", rating_mode="exact", db=self.db))
        self.assertEqual(get_ids(res_exact_quest), [2])

        res_exact_expl = asyncio.run(get_media_list(request=req, rating="explicit", rating_mode="exact", db=self.db))
        self.assertEqual(get_ids(res_exact_expl), [3])

    def test_get_random_media_rating_modes(self):
        # Exact explicit should only return media_expl id
        res = asyncio.run(get_random_media(rating="explicit", rating_mode="exact", db=self.db))
        self.assertEqual(res["id"], 3)

        # Exact questionable should only return media_quest id
        res = asyncio.run(get_random_media(rating="questionable", rating_mode="exact", db=self.db))
        self.assertEqual(res["id"], 2)

        # Exact safe should only return media_safe id
        res = asyncio.run(get_random_media(rating="safe", rating_mode="exact", db=self.db))
        self.assertEqual(res["id"], 1)

    def test_get_adjacent_media_rating_modes(self):
        # In exact questionable mode, adjacent media for id=2 should have no prev or next among safe/explicit
        res = asyncio.run(get_adjacent_media(media_id=2, rating="questionable", rating_mode="exact", db=self.db))
        self.assertIsNone(res.get("prev_id"))
        self.assertIsNone(res.get("next_id"))

        # In inclusive mode with rating="explicit", next for id=1 should be id=2 when order is asc
        res_inc = asyncio.run(get_adjacent_media(media_id=1, rating="explicit", rating_mode="inclusive", order="asc", db=self.db))
        self.assertEqual(res_inc.get("next_id"), 2)

    def test_albums_rating_modes(self):
        req = make_dummy_request()

        def get_album_names(res):
            return [a["name"] if isinstance(a, dict) else a.name for a in res["items"]]

        # Create 3 albums: one containing only safe, one questionable, one explicit
        a_safe = Album(id=1, name="Album Safe")
        a_quest = Album(id=2, name="Album Quest")
        a_expl = Album(id=3, name="Album Expl")
        self.db.add_all([a_safe, a_quest, a_expl])
        self.db.commit()

        self.db.execute(blombooru_album_media.insert().values([
            {"album_id": 1, "media_id": 1},
            {"album_id": 2, "media_id": 2},
            {"album_id": 3, "media_id": 3},
        ]))
        self.db.commit()

        # 1. get_albums inclusive vs exact
        albums_quest_inc = asyncio.run(get_albums(request=req, rating="questionable", db=self.db))
        inc_names = get_album_names(albums_quest_inc)
        self.assertIn("Album Safe", inc_names)
        self.assertIn("Album Quest", inc_names)
        self.assertNotIn("Album Expl", inc_names)

        albums_quest_exact = asyncio.run(get_albums(request=req, rating="questionable", rating_mode="exact", db=self.db))
        exact_names = get_album_names(albums_quest_exact)
        self.assertNotIn("Album Safe", exact_names)
        self.assertEqual(exact_names, ["Album Quest"])

        # 2. get_album_contents inclusive vs exact
        # In album 1 (containing media_safe), querying exact="questionable" should return 0 media
        contents_exact = asyncio.run(get_album_contents(request=req, album_id=1, rating="questionable", rating_mode="exact", db=self.db))
        self.assertEqual(len(contents_exact["media"]), 0)

        # Querying inclusive="questionable" should return media_safe (id=1)
        contents_inc = asyncio.run(get_album_contents(request=req, album_id=1, rating="questionable", db=self.db))
        self.assertEqual(len(contents_inc["media"]), 1)

    def test_search_related_tags_rating_modes(self):
        req = make_dummy_request()

        # Add unique tag to explicit media only
        tag_expl = Tag(id=2, name="nsfw_tag", category=TagCategoryEnum.general, post_count=1)
        self.db.add(tag_expl)
        self.db.commit()
        self.db.execute(blombooru_media_tags.insert().values([
            {"media_id": 3, "tag_id": 2}
        ]))
        self.db.commit()

        # Search related tags for query="cat" with rating="safe" (exact or inclusive) -> nsfw_tag should NOT be in results
        tags_safe = asyncio.run(search_related_tags(request=req, q="cat", rating="safe", rating_mode="exact", db=self.db))
        tag_names_safe = [t["name"] for t in tags_safe]
        self.assertNotIn("nsfw_tag", tag_names_safe)

        # Search related tags for query="cat" with rating="explicit" (exact) -> nsfw_tag should be present
        tags_expl = asyncio.run(search_related_tags(request=req, q="cat", rating="explicit", rating_mode="exact", db=self.db))
        tag_names_expl = [t["name"] for t in tags_expl]
        self.assertIn("nsfw_tag", tag_names_expl)

    def test_invalid_rating_value_fallback_all_endpoints(self):
        """Verify that invalid/malformed rating strings consistently fail closed to 'safe' in inclusive mode."""
        req = make_dummy_request()

        def get_ids(res):
            return [item["id"] if isinstance(item, dict) else item.id for item in res["items"]]

        # 1. search_media with invalid rating -> returns only safe media
        res_search = asyncio.run(search_media(request=req, rating="invalid_rating_123", db=self.db))
        self.assertEqual(get_ids(res_search), [1])

        # 2. get_media_list with invalid rating -> returns only safe media
        res_list = asyncio.run(get_media_list(request=req, rating="oops_nsfw", db=self.db))
        self.assertEqual(get_ids(res_list), [1])

        # 3. get_random_media with invalid rating -> returns safe media
        res_rand = asyncio.run(get_random_media(rating="garbage", db=self.db))
        self.assertEqual(res_rand["id"], 1)

        # 4. get_albums with invalid rating -> returns only safe albums
        a_safe = Album(id=10, name="Album Safe 10")
        a_expl = Album(id=11, name="Album Expl 11")
        self.db.add_all([a_safe, a_expl])
        self.db.commit()
        self.db.execute(blombooru_album_media.insert().values([
            {"album_id": 10, "media_id": 1},
            {"album_id": 11, "media_id": 3},
        ]))
        self.db.commit()

        res_albums = asyncio.run(get_albums(request=req, rating="invalid_rating", db=self.db))
        album_names = [a["name"] if isinstance(a, dict) else a.name for a in res_albums["items"]]
        self.assertIn("Album Safe 10", album_names)
        self.assertNotIn("Album Expl 11", album_names)

        # 5. get_album_contents with invalid rating -> returns safe media only and safe child albums only
        self.db.execute(blombooru_album_hierarchy.insert().values([
            {"parent_album_id": 10, "child_album_id": 11}
        ]))
        self.db.commit()

        res_contents = asyncio.run(get_album_contents(request=req, album_id=10, rating="invalid_rating", db=self.db))
        self.assertEqual(len(res_contents["media"]), 1)
        self.assertEqual(res_contents["media"][0].id, 1)
        # Child album 11 contains explicit media 3, so under invalid rating (fail-closed to safe) it should be omitted
        self.assertEqual(len(res_contents["albums"]), 0)

        # 6. search_related_tags with invalid rating -> excludes tags on non-safe media
        tag_expl2 = Tag(id=30, name="secret_nsfw", category=TagCategoryEnum.general, post_count=1)
        self.db.add(tag_expl2)
        self.db.commit()
        self.db.execute(blombooru_media_tags.insert().values([{"media_id": 3, "tag_id": 30}]))
        self.db.commit()

        tags_res = asyncio.run(search_related_tags(request=req, q="cat", rating="invalid_rating", db=self.db))
        tag_names = [t["name"] for t in tags_res]
        self.assertNotIn("secret_nsfw", tag_names)

        # 7. get_adjacent_media with invalid rating -> only navigates safe media
        res_adj = asyncio.run(get_adjacent_media(media_id=1, rating="invalid_rating", db=self.db))
        # Since only media 1 is safe, prev and next should both be None
        self.assertIsNone(res_adj.get("prev_id"))
        self.assertIsNone(res_adj.get("next_id"))

    def test_user_typed_rating_in_q_overrides_sidebar_rating(self):
        """Verify that user-typed rating in search query (q) takes precedence over top-level rating parameter."""
        req = make_dummy_request()

        def get_ids(res):
            return [item["id"] if isinstance(item, dict) else item.id for item in res["items"]]

        # Tag media 3 with tag 'dog'
        tag_dog = Tag(id=40, name="dog", category=TagCategoryEnum.general, post_count=1)
        self.db.add(tag_dog)
        self.db.commit()
        self.db.execute(blombooru_media_tags.insert().values([{"media_id": 3, "tag_id": 40}]))
        self.db.commit()

        # 1. search_media with top-level rating="safe" but query q="rating:explicit"
        # Should return media 3 (explicit) because user explicitly requested rating:explicit in search query
        res = asyncio.run(search_media(request=req, q="rating:explicit", rating="safe", db=self.db))
        self.assertEqual(get_ids(res), [3])

        # 2. search_related_tags with top-level rating="safe" but query q="cat rating:explicit"
        # Should include tags on explicit media 3
        tags_res = asyncio.run(search_related_tags(request=req, q="cat rating:explicit", rating="safe", db=self.db))
        tag_names = [t["name"] for t in tags_res]
        self.assertIn("dog", tag_names)

        # 3. get_adjacent_media with top-level rating="safe" but query q="rating:explicit"
        res_adj = asyncio.run(get_adjacent_media(media_id=3, q="rating:explicit", rating="safe", db=self.db))
        # Media 3 is matched and found within query context
        self.assertIn("prev_id", res_adj)

        # 4. get_album_contents with q="rating:explicit" and rating="safe"
        a = Album(id=50, name="Mixed Album")
        self.db.add(a)
        self.db.commit()
        self.db.execute(blombooru_album_media.insert().values([
            {"album_id": 50, "media_id": 1},
            {"album_id": 50, "media_id": 3},
        ]))
        self.db.commit()

        res_contents = asyncio.run(get_album_contents(request=req, album_id=50, q="rating:explicit", rating="safe", db=self.db))
        self.assertEqual(len(res_contents["media"]), 1)
        self.assertEqual(res_contents["media"][0].id, 3)

    def test_order_custom_fallback(self):
        """Verify that order:custom without valid comma-separated id: list falls back cleanly to default order."""
        req = make_dummy_request()

        def get_ids(res):
            return [item["id"] if isinstance(item, dict) else item.id for item in res["items"]]

        # 1. order:custom with no id: token -> query executes with default order fallback
        res1 = asyncio.run(search_media(request=req, q="order:custom", rating="explicit", db=self.db))
        self.assertEqual(len(get_ids(res1)), 3)

        # 2. order:custom with single id: token (no comma) -> query executes with fallback
        res2 = asyncio.run(search_media(request=req, q="order:custom id:1", rating="explicit", db=self.db))
        self.assertEqual(get_ids(res2), [1])

        # 3. order:custom with comma-separated id:3,1,2 -> applies custom order
        res3 = asyncio.run(search_media(request=req, q="order:custom id:3,1,2", rating="explicit", db=self.db))
        self.assertEqual(get_ids(res3), [3, 1, 2])

    def test_get_adjacent_media_all_three_paths(self):
        """Test all 3 branches in get_adjacent_media: non-album, album without q, album with q."""
        # Create an album with media 1 (safe), 2 (quest), 3 (expl)
        album = Album(id=100, name="Adjacent Test Album")
        self.db.add(album)
        self.db.commit()
        self.db.execute(blombooru_album_media.insert().values([
            {"album_id": 100, "media_id": 1},
            {"album_id": 100, "media_id": 2},
            {"album_id": 100, "media_id": 3},
        ]))
        self.db.commit()

        # Path 1: Album mode without q
        # 1a: exact questionable -> only media 2 matches, so prev/next are None
        res_p1_exact = asyncio.run(get_adjacent_media(media_id=2, mode="album", album_id=100, rating="questionable", rating_mode="exact", db=self.db))
        self.assertIsNone(res_p1_exact.get("prev_id"))
        self.assertIsNone(res_p1_exact.get("next_id"))

        # 1b: inclusive explicit with order=asc -> media 1 next is 2
        res_p1_inc = asyncio.run(get_adjacent_media(media_id=1, mode="album", album_id=100, rating="explicit", rating_mode="inclusive", order="asc", db=self.db))
        self.assertEqual(res_p1_inc.get("next_id"), 2)

        # Path 2: Album mode with q
        # 2a: exact questionable -> media 2 with q="cat"
        res_p2_exact = asyncio.run(get_adjacent_media(media_id=2, mode="album", album_id=100, q="cat", rating="questionable", rating_mode="exact", db=self.db))
        self.assertIsNone(res_p2_exact.get("prev_id"))
        self.assertIsNone(res_p2_exact.get("next_id"))

        # 2b: inclusive explicit with order=asc and q="cat"
        res_p2_inc = asyncio.run(get_adjacent_media(media_id=1, mode="album", album_id=100, q="cat", rating="explicit", rating_mode="inclusive", order="asc", db=self.db))
        self.assertEqual(res_p2_inc.get("next_id"), 2)

        # Path 3: Non-album search mode
        # 3a: exact questionable -> media 2
        res_p3_exact = asyncio.run(get_adjacent_media(media_id=2, mode="search", q="cat", rating="questionable", rating_mode="exact", db=self.db))
        self.assertIsNone(res_p3_exact.get("prev_id"))
        self.assertIsNone(res_p3_exact.get("next_id"))

        # 3b: inclusive explicit with order=asc
        res_p3_inc = asyncio.run(get_adjacent_media(media_id=1, mode="search", q="cat", rating="explicit", rating_mode="inclusive", order="asc", db=self.db))
        self.assertEqual(res_p3_inc.get("next_id"), 2)

    def test_config_and_schema(self):
        # Verify SettingsUpdate schema parses sidebar_rating_filter_mode
        su = SettingsUpdate(sidebar_rating_filter_mode="exact")
        self.assertEqual(su.sidebar_rating_filter_mode, "exact")

        # Verify config defaults and property
        self.assertEqual(settings.SIDEBAR_RATING_FILTER_MODE, "inclusive")

        settings.save_settings({"sidebar_rating_filter_mode": "exact"})
        self.assertEqual(settings.SIDEBAR_RATING_FILTER_MODE, "exact")

        # Restore default
        settings.save_settings({"sidebar_rating_filter_mode": "inclusive"})
        self.assertEqual(settings.SIDEBAR_RATING_FILTER_MODE, "inclusive")
