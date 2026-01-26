from Common import LoggingContext, config
from Server import Server

if __name__ == "__main__":

    with LoggingContext(__file__) as logging_context:

        server = Server(
            config=config.server,
            logging_context=logging_context,
        )
        server.run()
