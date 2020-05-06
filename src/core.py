from configs import conf
from p2p import P2P


class Core:
    """ Core class to run client/server """

    def run_threads(self, threads):
        [thread.start() for thread in threads]
        [thread.join() for thread in threads]
        print("[*] Threads started")

    def start_server(self):
        threads = [
            P2P(conf["SIGN_UP"]), P2P(conf["QUERY"]),
            P2P(conf["HEARTBEAT"]), P2P(conf["RETRIEVE"])]
        print("[-] Running server...")
        self.run_threads(threads)

    def start_client(self, *args):
        print("[-] Configuring to start client...")
        threads = []
        server_ip, services = args.client[0], args.__dict__
        for service in services:
            if services[service] is True:
                threads.append(client_threads_factory(service, server_ip))
        print("[-] Running client...")
        self.run_threads(threads)

    def client_threads_factory(self, service, server_ip):
        return {
            "SIGN_UP": P2P(conf["SIGN_UP"], server_ip, True),
            "HEARTBEAT": P2P(conf["HEARTBEAT"], server_ip, True),
            "QUERY": P2P(conf["QUERY"], server_ip, True),
            "RETRIEVE": P2P(conf["RETRIEVE"], server_ip, True)
        }.get(service.upper())
