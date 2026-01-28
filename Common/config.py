from dataclasses import dataclass
from tomllib import load

from dacite import from_dict

from .utils import root_dir

__all__ = (
    "PostgresConfig",
    "HTTPConfig",
    "APIConfig",
    "ClientConfig",
    "ServerConfig",
    "AutopilotConfig",
    "GlobalConfig",
    "config",
)


@dataclass(kw_only=True, frozen=True)
class PostgresConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    min_connection_pool_size: int
    max_connection_pool_size: int


@dataclass(kw_only=True, frozen=True)
class HTTPConfig:
    max_retries: int
    max_sleep_time: float
    handle_ratelimits: bool
    max_retry_after: float
    handle_backoffs: bool
    backoff_factor: float
    backoff_start: float
    backoff_cap: float


@dataclass(kw_only=True, frozen=True)
class APIConfig:
    host: str
    port: int
    domain: str
    secure: bool
    local: bool
    http: HTTPConfig


@dataclass(kw_only=True, frozen=True)
class ClientConfig:
    api: APIConfig


@dataclass(kw_only=True, frozen=True)
class ServerConfig:
    host: str
    port: int
    proxy: bool
    max_tokens_per_user: int
    access_time: float
    refresh_time: float
    ws_heartbeat: float
    ws_max_message_size: int
    ws_message_limit: int
    ws_message_interval: float
    resource_grace: float
    task_interval: float
    max_process_pool_workers: int
    postgres: PostgresConfig


@dataclass(kw_only=True, frozen=True)
class AutopilotConfig:
    api: APIConfig
    postgres: PostgresConfig


@dataclass(kw_only=True, frozen=True)
class GlobalConfig:
    client: ClientConfig
    server: ServerConfig
    autopilot: AutopilotConfig


config_file_path = root_dir() / "config.toml"

with config_file_path.open("rb") as config_file:
    config_data = load(config_file)

config = from_dict(GlobalConfig, config_data)  # noqa
