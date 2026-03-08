"""Tests for database module"""
import pytest
from app.database import init_db, get_db, engine, SessionLocal
from app.models import Base


class TestDatabase:
    """Test database functions"""

    def test_init_db(self):
        """Test database initialization"""
        # init_db should not raise an exception
        init_db()

    def test_get_db_generator(self):
        """Test get_db yields a database session"""
        # get_db is a generator, we can iterate it
        db_gen = get_db()
        db = next(db_gen)
        # Should have a close method
        assert hasattr(db, 'close')
        # Clean up the generator
        try:
            next(db_gen)
        except StopIteration:
            pass

    def test_session_local_creation(self):
        """Test SessionLocal can create sessions"""
        session = SessionLocal()
        assert session is not None
        session.close()
