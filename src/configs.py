import os
from os.path import join, dirname
# Third-party libraries
import dotenv

dotenv_path = dotenv.find_dotenv('config.dotenv')
dotenv.load_dotenv(dotenv_path)


def config():
    """ 
        Ensure that env has all needed variables to execute the app
    """
    return {
        # heartbeat timeout counter
        "HEARTBEAT_TIMEOUT": int(os.environ.get("HEARTBEAT_TIMEOUT")),
        # timeout to disconnect the client if it cannot reach a host
        "TIMEOUT": int(os.environ.get("TIMEOUT")),
        # time in seconds to receive/send heartbeat
        "HEARTBEAT_TIME": int(os.environ.get("HEARTBEAT_TIME")),
        "BUFFERSIZE": int(os.environ.get("BUFFERSIZE")),  # buffer size to sockets
        # ---------- Service configurations ports -------------
        "SIGN_UP": int(os.environ.get("SIGN_UP")),
        "QUERY": int(os.environ.get("QUERY")),
        "HEARTBEAT": int(os.environ.get("HEARTBEAT")),
        "RETRIEVE": int(os.environ.get("RETRIEVE")),
        "SEND": int(os.environ.get("SEND"))
    }

conf = config()
