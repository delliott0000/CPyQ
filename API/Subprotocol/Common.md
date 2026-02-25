# Introduction
This file documents shared behaviour and workflows that are used in the WebSocket subprotocol.

It is recommended to read through [HTTP](../HTTP) in its entirety first; this subfolder will reference some things that are defined there.

# Scope & Purpose
The subprotocol only defines application-level messages and behaviours. Transport semantics, such as connection liveliness and message size limits, are handled solely at the WebSocket level and are not documented here.

Before we get into the details, a reminder of the purpose of this subprotocol:
- Send & receive `States` for syncing and store them for later recovery.
- Defer resource-intensive tasks, such as file generation, to an `Autopilot`.

The subprotocol assumes that one peer will act as the server and the other as a client. Communication between two peers is mechanically symmetric. That is to say that the same rules surrounding [Message Flow](#message-flow) and [Message Structure](#message-structure) apply in either direction of travel. However, the [Handshake Phase](#connection-phases) as well as the [Contents](Contents) of messages are asymmetric, meaning that each peer has distinct responsibilities during setup and communication.

# Message Flow
Each message must be an `Event` or an `Ack`. An `Event` contains information - this could be a request ("perform X") or a notification of an outcome ("X complete"). An `Ack` acknowledges that an `Event` has been received and parsed, but does not imply successful processing/execution.

The following rules define the `Event`/`Ack` message flow:
- Each `Event` must be assigned a Universally Unique Identifier (UUID).
- Each `Event` must be acknowledged exactly once, within the time limit supplied by the server during the [Handshake Phase](#connection-phases).
- Each `Ack` must reference an `Event` by specifying the UUID of that `Event`.
- Each `Ack` must reference an `Event` that exists and has not already been acknowledged.
- `Events` and `Acks` may be sent & received out of order.

Please note that while UUIDs should ideally be unique within the scope of the WebSocket connection, this is not strictly required in practice. An implementation may discard an outgoing `Event` and its UUID as soon as it has been acknowledged - this is actually recommended to reduce the memory usage of a long-lasting or high-throughput connection. Therefore, a sending peer is only required to ensure UUID uniqueness within its current set of unacknowledged outgoing `Events`.  Peers may generate UUIDs using any method they choose.

Message flow must immediately terminate when a violation of the subprotocol occurs or when the WebSocket closing handshake begins. Implementations should abort any in-progress processing of messages received prior to prevent further messages from being emitted.

# Message Structure
Each message must be a text frame that can be parsed into a valid JSON object.

Below is a list of top-level fields and their corresponding types and enumerations for each message type.

Each field is mandatory unless `None` is listed as an allowed type, in which case that field is optional. Omitting an optional field should be interpreted in the same way as an explicit `None` for that field.

`Event` fields:
```py
{
    "type": "event",  # By definition; Enum ["event"]
    "id": str,  # UUID
    "sent_at": str,  # ISO 8601
    "status": str,  # Enum ["normal", "error", "fatal"]
    "reason": str | None,  # For logging and traceback
    "payload": dict[str, Any]  # Actual data
}
```

`Ack` fields:
```py
{
    "type": "ack",  # By definition; Enum ["ack"]
    "id": str,  # UUID of an Event
    "sent_at": str  # ISO 8601
}
```

The `"status"` field describes the outcome of an `Event`. Unless the value is `"fatal"`, this field does not mandate any specific behaviour from the receiving peer.
- `"normal"` indicates that an `Event` took place without error.
- `"error"` indicates that a recoverable application-level error has occurred. The connection may remain open.
- `"fatal"` indicates that an unrecoverable application-level error has occurred. The connection must immediately close.

The `"reason"` field is an optional, human-readable string for logging, debugging and so on. This field does not mandate any specific behaviour from the receiving peer.

The `"payload"` field contains the actual data associated with an `Event`. Its semantics are defined in [Connection Phases](#connection-phases) and [Contents](Contents).

The following rules apply to top-level fields, but not payload-level fields.

It *is* a violation of the subprotocol to:
- Miss a mandatory field.
- Supply a value of an incorrect type.
- Supply a value that is not a member of the field's designated enumeration or is otherwise structurally invalid. (For instance, ISO 8601 strings.)

It *is not* a violation of the subprotocol to:
- Supply an undocumented field. The receiving peer can safely ignore this.

# Connection Phases
Each connection is divided into two application-level phases; the handshake phase and the messaging phase.

The handshake phase begins as soon as the WebSocket connection is established. During this phase, the server declares a set of policies to which the client must consent. These policies are sent in the form of an `Event` payload. The client must acknowledge this `Event`, at which point the handshake phase ends and the messaging phase begins. The client is not given any means to negotiate these policies. All other communication must take place entirely within the messaging phase, which lasts until the WebSocket connection closes.

...

# Close Codes
If and only if a peer violates the subprotocol, then the other peer must immediately close the WebSocket connection with the appropriate close code without sending any further messages (including any pending `Acks`).

Close codes and their corresponding failure scenarios:
- **4001** - A message is not a text frame.
- **4002** - A message cannot be parsed into a valid JSON object.
- **4003** - A message is missing a mandatory field.
- **4004** - A message supplies a value of an incorrect type.
- **4005** - A message supplies a value that is not a member of the field's designated enumeration or is otherwise structurally invalid. (This may take precedence over type errors due to implementation details.)
- **4006** - Two or more unacknowledged `Events` sent by the same peer share the same UUID.
- **4007** - An `Event` is not acknowledged within the acknowledgement time limit.
- **4008** - An `Ack` references an `Event` that does not exist or has already been acknowledged.
- **4009** - An `Event` contains `"status": "fatal"`. Upon sending or receiving such `Event`, the peer must immediately close the connection using this close code.

Not part of the subprotocol per se, but still application-specific:
- **4000** - Sent by the server when the `Token` that was used to open the WebSocket connection is no longer valid.
- **4999** - Sent by either peer when an internal error is encountered.

# Final Notes
...