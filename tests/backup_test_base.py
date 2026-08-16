import io
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.config import settings
from backend.app.database import Base
from backend.app.models import (Album, BooruConfig, Media, Tag, TagAlias,
                                TagImplication, blombooru_album_hierarchy,
                                blombooru_album_media,
                                blombooru_implication_implied,
                                blombooru_implication_targets,
                                blombooru_media_tags)

def make_dummy_jpeg() -> bytes:
    """Generates a minimal valid JPEG image bytes for tests."""
    buf = io.BytesIO()
    img = Image.new("RGB", (32, 32), color="red")
    img.save(buf, format="JPEG")
    return buf.getvalue()

class BackupTestBase(unittest.TestCase):
    """Base test class providing temporary filesystem sandboxes, test database, and settings isolation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.temp_dir)

        db_file = self.tmp_path / "test.db"
        self.engine = create_engine(f"sqlite:///{db_file}")
        Base.metadata.create_all(bind=self.engine)
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.TestingSessionLocal()

        self.original_dir = self.tmp_path / "media" / "original"
        self.thumb_dir = self.tmp_path / "media" / "thumbnails"
        self.data_dir = self.tmp_path / "data"
        self.custom_themes_dir = self.data_dir / "custom_themes"

        self.original_dir.mkdir(parents=True, exist_ok=True)
        self.thumb_dir.mkdir(parents=True, exist_ok=True)
        self.custom_themes_dir.mkdir(parents=True, exist_ok=True)

        self.old_base = settings.BASE_DIR
        self.old_orig = settings.ORIGINAL_DIR
        self.old_thumb = settings.THUMBNAIL_DIR
        self.old_data = settings.DATA_DIR
        self.old_settings_file = settings.SETTINGS_FILE
        self.old_settings_dict = dict(settings.settings)
        self.old_file_settings_dict = dict(settings.file_settings)

        settings.BASE_DIR = self.tmp_path
        settings.ORIGINAL_DIR = self.original_dir
        settings.THUMBNAIL_DIR = self.thumb_dir
        settings.DATA_DIR = self.data_dir
        settings.SETTINGS_FILE = self.data_dir / "settings.json"
        settings.file_settings = {}
        settings.settings = settings._get_default_settings()

    def tearDown(self):
        self.db.close()
        settings.BASE_DIR = self.old_base
        settings.ORIGINAL_DIR = self.old_orig
        settings.THUMBNAIL_DIR = self.old_thumb
        settings.DATA_DIR = self.old_data
        settings.SETTINGS_FILE = self.old_settings_file
        settings.file_settings = self.old_file_settings_dict
        settings.settings = self.old_settings_dict
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def wipe_database(self):
        self.db.execute(blombooru_album_hierarchy.delete())
        self.db.execute(blombooru_album_media.delete())
        self.db.execute(blombooru_media_tags.delete())
        self.db.execute(blombooru_implication_targets.delete())
        self.db.execute(blombooru_implication_implied.delete())
        self.db.query(TagImplication).delete()
        self.db.query(BooruConfig).delete()
        self.db.query(Album).delete()
        self.db.query(Media).delete()
        self.db.query(TagAlias).delete()
        self.db.query(Tag).delete()
        self.db.commit()
