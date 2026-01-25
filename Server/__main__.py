from Common import config, setup_logging
from Server import Server

setup_logging(__file__)

if __name__ == "__main__":
    server = Server(config=config.server)
    server.run()
