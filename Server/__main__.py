from Common import LoggingContext, config
from Server import Server

if __name__ == "__main__":
    with LoggingContext(__file__):
        server = Server(config=config.server)
        server.run()
