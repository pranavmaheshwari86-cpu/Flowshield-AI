"""
apps/api/app/utils/ssl_context.py
Flowshield — Centralized SSL Context Utility for External Meteorological APIs
Ensures valid certificate authorities via certifi across macOS, Linux, and Windows.
"""

import ssl
import certifi
import logging

logger = logging.getLogger("flowshield.ssl_context")


def get_ssl_context() -> ssl.SSLContext:
    """Returns an SSL context configured with Mozilla's root CA bundle from certifi."""
    try:
        cafile = certifi.where()
        return ssl.create_default_context(cafile=cafile)
    except Exception as e:
        logger.debug(f"Failed to create certifi SSL context: {e}, falling back to default")
        return ssl.create_default_context()


def configure_ssl_context():
    """Globally configures Python's default HTTPS context to use certifi."""
    try:
        cafile = certifi.where()
        ssl._create_default_https_context = lambda *args, **kwargs: ssl.create_default_context(cafile=cafile, *args, **kwargs)
        logger.info(f"Configured global HTTPS SSL context with certifi CA bundle: {cafile}")
    except Exception as e:
        logger.warning(f"Could not configure global SSL context: {e}")
