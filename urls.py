"""Delegate to the inner project's URLConf.
This ensures a single source of truth for routes and the SPA catch-all.
Also re-export serve_frontend so reverse lookups to mywork.urls.serve_frontend work.
"""
from mywork.mywork.urls import urlpatterns, serve_frontend  # noqa: F401
