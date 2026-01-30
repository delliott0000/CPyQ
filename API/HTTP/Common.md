# Introduction
This file documents shared behaviour and definitions that are used across all HTTP endpoints.

Before we can jump straight in, we must first define a few things, and consider our end goals for the API.

# Definitions
- **Client** - A normal, "human" client application.
- **Autopilot** - An automated, headless client application.
- **User** - `Clients` and `Autopilots` are collectively referred to as `Users`.
- **Instance** - A running copy of the program that a `User` is using to interact with the API.
- **Session** - A temporary context that keeps track of `User` activity, independent of authentication.
- **Resource** - An abstract entity that `Sessions` can acquire, release, read from, and write to.
- **State** - A container for a `Session's` real-time snapshot.
- **Task** - A job that is offloaded from the server to an `Autopilot`.

# Considerations
- `Users` can have many ongoing `Sessions`.
- `Users` can recover previous `Sessions` by supplying the `Session's` ID.
- Therefore, two or more `Instances` that belong to the same `User` account, may share the same `Session`. In this case, their `States` are automatically synced together.
- Each `Session` can acquire up to one `Resource` at a time; each `Resource` can be acquired by up to one `Session` at a time. These restrictions prevent race conditions, since a `Session` must acquire a `Resource` before modifying it.
- If a `Session` is owned by an `Autopilot`, then it cannot interact with `Resources`, and its `State` is functionally inert.
- `Autopilots` can perform `Tasks` that require a lot of system resources and/or time. This keeps the server freed up to continue communicating with `Users`.

# Models
With all of this in mind, we will organise the functionality of the server into the following models. Each bullet point includes a JSON-like representation of the model that it describes. Fields marked `ISO 8601` follow the format `%Y-%m-%dT%H:%M:%S.%f%z`.
- **User** - See [Definitions](#definitions).
```py
{
    "id": int,
    "username": str,
    "display_name": str | None,
    "email": str | None,
    "autopilot": bool,
    "admin": bool
}
# Omitted the "teams" field; this is not relevant here.
```
- **State** - See [Definitions](#definitions). This is stored by the server mainly to prevent loss of progress.
```py
{
}
# TODO: Define fields and types.
```
- **Resource** - See [Definitions](#definitions). Different `Resource` types will implement their own fields. `Resource` fields also depend on the context of the request. Every `Resource` is owned by a `User`; the owner might not be the `User` whose `Session` has temporarily acquired the `Resource`.
```py
{
    "id": int,
    "owner": User
}
# All resources must include these fields as a bare minimum.
```
- **Session** - See [Definitions](#definitions). Each `Session` is associated with a `User` (many-to-one), a `State` (one-to-one) and the `Resource` that it currently has acquired (one-to-one).
```py
{
    "id": str,
    "user": User,
    "state": State,
    "resource": Resource | None  # Metadata only
}
```
- **Token** - An authentication context. `Users` exchange their username and password for a `Token`. Each `Token` is associated with a `Session` (many-to-one).
```py
{
    "access": str,
    "refresh": str,
    "access_expires": str,  # ISO 8601
    "refresh_expires": str,  # ISO 8601
    "killed_at": str | None,  # ISO 8601 or None
    "session": Session
}
```

# Groups and Rules
Endpoints are arranged into groups based on their functionality. These groups collectively make up the API.

Rules describe how endpoints behave. These are divided into API-level, group-level, and endpoint-level rules.

Aside from the noted exceptions, API-level rules apply to all endpoints in the API. Group-level rules apply to all endpoints in the given group. Endpoint-level rules only apply to the given endpoint.

API-level rules take precedence over group-level rules, which take precedence over endpoint-level rules.

API-level rules are listed below in descending order of precedence.

## Request and Response Structures
Most endpoints expect the caller to supply a JSON object with specific fields. Other endpoints don't expect a JSON object at all. Unexpected JSON objects/fields will be ignored and will not cause an error to be returned.

The API will return a JSON object with every response, except for successful WebSocket upgrades.

For unsuccessful requests, this object will contain a `"message": ...` field describing what went wrong.

For successful requests, this object will contain `"message": "OK"` along with the other documented fields.

## Authentication
Except for `/auth/login` and `/auth/refresh`, every endpoint requires an `"Authorization": "Bearer ..."` header, where `...` is a `Token` access key.

If the `Authorization` header is missing, is of the wrong type, or cannot be parsed, the API will return `400 Bad Request`.

If the `Authorization` header is incorrect, the API will return `401 Unauthorized`.

## Client/Autopilot/Admin-Only
Endpoints can be `Client-only`, `Autopilot-only` or `Admin-only`. An `Admin` is simply a `User` with elevated permissions.

If a `User` sends a request to one of these endpoints and does not meet the required criteria, the API will return `403 Forbidden`.

This will be clarified on a per-endpoint basis. Some endpoints don't enforce any of these requirements, such as `/auth/login`.

## Rate Limits
Every endpoint is rate limited. Rate limits can be applied per endpoint, per `Token`, per `User` or per IP address. Exact rate limits are not published in this documentation.

If a request is rate limited, the API will return `429 Too Many Requests`.

Whilst not strictly HTTP-related, it should also be noted that if a client application sends too many messages over a WebSocket connection in quick succession, the server may close the connection with close code `1008` (Policy Violation).

## Success
If a request is considered successful, the API will return `200 OK`. This does not include WebSocket upgrades.

# Final Notes
For further details on individual groups and endpoints, please see [Contents](Contents). Each file in this folder documents one group, and includes the following:
- A list of group-level rules, listed in descending order of precedence.
- A number of sections, each documenting one endpoint.

Each section will include the following:
- A brief description of the endpoint.
- The JSON object that the client application should supply with their request. If this information is omitted from a given section, then the API does not expect a JSON object to be supplied when sending a request to the corresponding endpoint.
- The JSON object that the API will return if the request is successful.
- Other endpoint-level rules, listed in descending order of precedence.
- Any additional information, such as whether the endpoint is restricted to a certain type of `User`.