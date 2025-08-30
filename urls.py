"""Delegate to the inner project's URLConf.
This ensures a single source of truth for routes and the SPA catch-all.
"""
from mywork.mywork.urls import urlpatterns  # noqa: F401
