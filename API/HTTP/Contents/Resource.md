# Resource Endpoints
This file documents the group of endpoints related to `Resources`.

If you haven't already, please read [Common.md](../Common.md) first.

## Group-Level Rules
- Each endpoint path follows the pattern `/resource/{type}/{id}/{operation}`.
- If `{operation}` is not recognised, the API will return `404 Not Found`.
- If `{id}` is not an integral string, or `{type}` is not recognised, the API will return `400 Bad Request`.
- If `{id}` is not found, the API will return `404 Not Found`.

## POST /resource/{type}/{id}/acquire
Acquire a `Resource`. Most interactions between a `Session` and a `Resource` will fail if the `Session` has not acquired the `Resource`. If a `Session` that has acquired a `Resource` does not have at least one `Token` with an open WebSocket connection, the server will automatically release the `Resource` within a short time period without warning.

Returned by the API:
```py
{
    "resource": Resource  # Metadata only
}
```

- If the requesting `User` does not have the required permissions, the API will return `403 Forbidden`.
- If the requesting `Session` has already acquired any `Resource`, or the requested `Resource` has already been acquired by any `Session`, the API will return `409 Conflict`.

This endpoint is `Client-only`.

## POST /resource/{type}/{id}/release
Release a `Resource`, allowing it to be acquired by another `Session`. Permission checks are not performed here.

Returned by the API:
```py
{
    "resource": Resource  # Metadata only
}
```

- If the requesting `Session` has not acquired the requested `Resource`, the API will return `409 Conflict`.

This endpoint is `Client-only`.

## GET /resource/{type}/{id}/preview
Retrieve some basic information about a `Resource`. Different `Resource` types will implement their own previews. Acquisition checks are not performed here.

Returned by the API:
```py
{
    "resource": Resource  # Preview only
}
```

- If the requesting `User` does not have the required permissions, the API will return `403 Forbidden`.

This endpoint is `Client-only`.

## GET /resource/{type}/{id}/view
Retrieve all information about a `Resource`. Different `Resource` types will implement their own views.

Returned by the API:
```py
{
    "resource": Resource  # Full view
}
```

- If the requesting `User` does not have the required permissions, the API will return `403 Forbidden`.
- If the requesting `Session` has not acquired the requested `Resource`, the API will return `409 Conflict`.

This endpoint is `Client-only`.