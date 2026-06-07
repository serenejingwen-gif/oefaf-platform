"""SD-MAC public analytics API package.

A FastAPI application exposing read access to GEA, CRICAT, and SD-MAC analytics
record types over the platform schema registry, plus a POST endpoint for
creating capacity-allocation scenarios. The application is served entirely from
bundled synthetic fixtures and the schema-registry manifests; it makes no
network calls and reads no proprietary or employer-internal data.

All data served by this API is synthetic illustrative data generated for
demonstration. It is NOT real agency data and is NOT derived from any
proprietary or employer source.

Public symbols:
    app   -- the FastAPI application instance (``sdmac.api.main.app``).
"""

from sdmac.api.main import app

__all__ = ["app"]
