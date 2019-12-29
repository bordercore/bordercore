"""Development settings and globals."""

from __future__ import absolute_import

from .base import *

DEBUG = True

for t in TEMPLATES:
    t['OPTIONS']['debug'] = True

INTERNAL_IPS = ('127.0.0.1', '10.3.2.2')

# Elasticsearch config
ELASTICSEARCH_ENDPOINT = "http://localhost:9200"

MIDDLEWARE += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INSTALLED_APPS += (
    'debug_toolbar',
    'django_extensions',
    'notebook',
    'template_timings_panel',
)

DEBUG_TOOLBAR_PANELS = (
    'template_timings_panel.panels.TemplateTimings.TemplateTimings',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.versions.VersionsPanel'
)
