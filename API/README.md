# CPyQ Server API
This module documents the behaviour of the web API exposed by the [Server](../Server) module. It serves as a reference point for related development.

The API uses the [HTTP](https://www.rfc-editor.org/rfc/rfc2616) and [WebSocket](https://www.rfc-editor.org/rfc/rfc6455) communication protocols. It is assumed that the reader is familiar with both of these protocols. The API also uses a custom subprotocol layered on top of WebSocket to keep interactions well-defined and predictable.

The module is organised into the following subfolders:
- [HTTP](HTTP) - Covers HTTP endpoints, response codes and data structures. This includes WebSocket upgrades. It is recommended to start here.
- [Subprotocol](Subprotocol) - Describes the subprotocol that applications should follow when communicating via WebSocket.

Each subfolder includes:
- `Common.md` - Provides shared logic, definitions and utilities used throughout the subfolder.
- `Contents` - Details endpoints, messages or workflows specific to a given scenario.