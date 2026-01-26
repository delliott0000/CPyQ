from Common import config, setup_logging
from Server import Server

if __name__ == "__main__":
    setup_logging(__file__)
    server = Server(config=config.server)
    server.run()
