from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import close_old_connections
import logging

logger = logging.getLogger(__name__)


class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Ensure db connections are clean
        close_old_connections()

        # Default to anonymous
        scope['user'] = AnonymousUser()

        try:
            # Read token from query string: ws://.../ws/chat/<id>/?token=...
            query_string = scope.get('query_string', b'').decode()
            params = parse_qs(query_string)
            token = params.get('token', [None])[0]

            if token:
                authenticator = JWTAuthentication()
                validated = authenticator.get_validated_token(token)
                user = authenticator.get_user(validated)
                scope['user'] = user
                logger.info(f"WS Auth OK: user_id=%s path=%s", getattr(user, 'id', None), scope.get('path'))
            else:
                logger.info("WS Auth: no token in query string for path %s", scope.get('path'))
        except Exception:
            # Keep AnonymousUser on any error
            logger.warning("WS Auth failed; treating as anonymous. Path=%s", scope.get('path'))

        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(inner)
