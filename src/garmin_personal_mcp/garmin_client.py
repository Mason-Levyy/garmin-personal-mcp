from collections.abc import Callable

from garmin_personal_api import (
    GarminPersonalApiClient,
    GarminPersonalApiError,
    HttpError,
    PersonalApiAuthenticator,
    resolve_api_key,
)

KEY_PAGE = "https://connect.garmin.com/app/settings/personalApiToken"
RECONNECT_HINT = (
    f"Create a key at {KEY_PAGE} and run `garmin-personal-mcp auth` "
    "(or set GARMIN_PERSONAL_API_KEY)."
)
UNAUTHORIZED = 401
KEY_REJECTED_STATUSES = {400, 401, 403}


class ApiKeyError(RuntimeError):
    pass


def bearer_token(
    authenticator: PersonalApiAuthenticator,
    api_key: str | None,
    *,
    force_refresh: bool,
) -> str:
    try:
        key = resolve_api_key(api_key)
        token = authenticator.obtain_token(key, force_refresh=force_refresh)
    except HttpError as exc:
        if exc.status_code not in KEY_REJECTED_STATUSES:
            raise
        raise ApiKeyError(
            f"Garmin rejected the Personal API key (HTTP {exc.status_code}); it "
            f"may have expired or been deleted. {RECONNECT_HINT}"
        ) from exc
    except GarminPersonalApiError as exc:
        raise ApiKeyError(f"{exc} {RECONNECT_HINT}") from exc
    return token.access_token


def run[T](op: Callable[[GarminPersonalApiClient], T], access_token: str) -> T:
    with GarminPersonalApiClient(access_token) as client:
        return op(client)


def call[T](
    op: Callable[[GarminPersonalApiClient], T], *, api_key: str | None = None
) -> T:
    """Bearer tokens can be revoked before their exp claim, so a 401 gets one
    retry with a freshly exchanged token."""
    with PersonalApiAuthenticator() as authenticator:
        try:
            return run(op, bearer_token(authenticator, api_key, force_refresh=False))
        except HttpError as exc:
            if exc.status_code != UNAUTHORIZED:
                raise
        return run(op, bearer_token(authenticator, api_key, force_refresh=True))
