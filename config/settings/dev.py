"""Development settings and globals."""

from __future__ import absolute_import

from .base import *

DEBUG = True

for t in TEMPLATES:
    t['OPTIONS']['debug'] = True

INTERNAL_IPS = ('127.0.0.1', '10.3.2.2')

MIDDLEWARE += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INSTALLED_APPS += (
    'debug_toolbar',
    'template_timings_panel',
)

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'template_timings_panel.panels.TemplateTimings.TemplateTimings'
)
