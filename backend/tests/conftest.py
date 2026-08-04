"""Pytest fixtures for backend foundation tests."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Configure testing environment before Settings / app import side effects
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DATABASE_REQUIRED_ON_STARTUP"] = "false"
os.environ["DATABASE_CONNECT_RETRIES"] = "1"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["LOG_JSON"] = "false"
os.environ["DEBUG"] = "true"


@pytest.fixture()
def settings():
    from app.core.config import clear_settings_cache, get_settings
    from app.database.session import reset_engine

    clear_settings_cache()
    reset_engine()
    return get_settings()


@pytest.fixture()
def app(settings):
    from app.main import create_app

    return create_app()


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client
