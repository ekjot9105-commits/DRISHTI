"""
Notification package.

Importing this package registers every built-in channel with the registry in
`dispatcher.py`. The single fan-out entry point is `dispatch(alert)`.
"""
from app.services.notify.dispatcher import (  # noqa: F401
    Channel,
    NotificationEvent,
    dispatch,
    dispatch_and_wait,
    get_channels,
    register,
)

# Import side effects register the channels. Keep new channels listed here.
from app.services.notify import null   # noqa: F401,E402
from app.services.notify import email  # noqa: F401,E402
