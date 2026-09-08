"""
Detector plugin package.

Importing this package registers every built-in detector with the registry in
`base.py`. `ml_inference` runs all registered detectors once per processed frame.
"""
from app.services.detectors.base import (  # noqa: F401
    Detector,
    DetectorContext,
    register,
    get_detectors,
)

# Import side effects register the detectors. Keep new detectors listed here.
from app.services.detectors import fight  # noqa: F401,E402
from app.services.detectors import fire   # noqa: F401,E402
from app.services.detectors import crash  # noqa: F401,E402
