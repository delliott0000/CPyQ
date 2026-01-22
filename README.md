[![Python Version](https://img.shields.io/badge/Python-3.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/Code%20Style-Black-000000.svg)](https://github.com/psf/black)
[![Imports: iSort](https://img.shields.io/badge/Imports-iSort-ef8336.svg)](https://github.com/PyCQA/isort)

**Still in early development.**

# CPyQ
CPyQ is a Python-based "Configure, Price, Quote" (CPQ) platform. The project was originally started with steel door configurations in mind. However, it is highly adaptable and can support a wide range of products across various industries.

The project is split into a few different modules:
- [Client](Client) - The front-end program that the user interacts with directly.
- [Server](Server) - Communicates user sessions and specification states with the client.
- [Autopilot](Autopilot) - Allows the server to offload certain tasks, such as generating documents.
- [Common](Common) - Defines objects and utilities used across multiple modules.
- [SQL](SQL) - Tools used for PostgreSQL setup/development.
- [API](API) - Documentation of the API exposed by the server.

# Features
- Web API that manages user sessions and enforces rate limits.
- Real-time communication of client states via WebSocket to prevent the loss of progress in the event of a crash.
- Use of the `asyncio` framework to handle many IO-bound tasks concurrently.
- Support for many autopilots running simultaneously.