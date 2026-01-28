from Common import LoggingContext, config
from Server import Server

if __name__ == "__main__":

    with LoggingContext("Server") as log_ctx:

        server = Server(
            config=config.server,
            log_ctx=log_ctx,
        )
        server.run()
