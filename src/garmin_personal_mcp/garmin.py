from collections.abc import Callable

from garmin_personal_api import (
    GarminPersonalApiClient,
    GarminPersonalApiError,
    HttpError,
    PersonalApiAuthenticator,
    resolve_api_key,
)

KEY_HINT = (
    "Create a key at https://connect.garmin.com/app/settings/personalApiToken and "
    "save it to ~/.config/garmin/connect-personal-api-key (chmod 600), or set "
    "GARMIN_PERSONAL_API_KEY."
)
UNAUTHORIZED = 401


class ApiKeyError(RuntimeError):
    pass


def bearer_token(authenticator: PersonalApiAuthenticator, force_refresh: bool) -> str:
    try:
        api_key = resolve_api_key()
        return authenticator.obtain_token(
            api_key, force_refresh=force_refresh
        ).access_token
    except HttpError as exc:
        raise ApiKeyError(
            f"Garmin rejected the Personal API key ({exc}). {KEY_HINT}"
        ) from exc
    except GarminPersonalApiError as exc:
        raise ApiKeyError(f"{exc} {KEY_HINT}") from exc


def run[T](op: Callable[[GarminPersonalApiClient], T], access_token: str) -> T:
    with GarminPersonalApiClient(access_token) as client:
        return op(client)


def call[T](op: Callable[[GarminPersonalApiClient], T]) -> T:
    """Bearer tokens can be revoked before their exp claim, so a 401 gets one
    retry with a freshly exchanged token."""
    with PersonalApiAuthenticator() as authenticator:
        try:
            return run(op, bearer_token(authenticator, force_refresh=False))
        except HttpError as exc:
            if exc.status_code != UNAUTHORIZED:
                raise
        return run(op, bearer_token(authenticator, force_refresh=True))


def read_sections(
    client: GarminPersonalApiClient,
    sections: dict[str, Callable[[GarminPersonalApiClient], object]],
) -> dict:
    """Garmin answers 4xx for data that doesn't exist yet (e.g. today's HRV
    before you've slept), so one missing section shouldn't sink the rest."""
    record = {}
    for name, read in sections.items():
        try:
            record[name] = read(client)
        except HttpError as exc:
            if exc.status_code == UNAUTHORIZED:
                raise
            record[name] = {"error": str(exc)}
    return record
