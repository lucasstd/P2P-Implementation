import argparse
from core import Core


def main():
    ap = argparse.ArgumentParser(description="P2P - Cliente server", prog="app")
    ap.add_argument("-c", "--client", metavar="SERVER", nargs=1,
                    help="Start as a client. Needs to specify host as " \
                    "parameter and service in another flag.")
    # TODO: describe better
    ap.add_argument(
        "-su", "--sign_up", action='store_true', help="Execute sign up service.")
    ap.add_argument(
        "-s", "--server", action='store_true', help="Start as a server.")
    ap.add_argument(
        "-hb", "--heartbeat", action='store_true', help="Execute heartbeat service.")
    ap.add_argument(
        "-r", "--retrieve", action='store_true', help="Execute retrieve service.")
    ap.add_argument(
        "-q", "--query", action='store_true', help="Execute query service.")

    args = ap.parse_args()
    print(f"Arguments recieved: {args}")
    core = Core()
    if args.client: core.start_client(args)
    elif args.server: core.start_server()
    else:
        print("Didn't start the server nor run a client with a service.")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
