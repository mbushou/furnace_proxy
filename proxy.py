#!/usr/bin/python3

# -------------------------
# Furnace (c) 2017-2018 Micah Bushouse
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -------------------------

import os
import sys
import threading
import time
import argparse

import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator


def tprint(msg):
    """
    Print immediately with newline.
    :param msg: The text to be printed.
    """
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def tprintn(msg):
    """
    Print immediately without newline.
    :param msg: The text to be printed.
    """
    sys.stdout.write(msg)
    sys.stdout.flush()


class RouterProxyRuntime(threading.Thread):

    """
    Proxies between the proxy-router and the backend-dealer sockets.
    """

    def __init__(
        self,
        ctx,
        kp,
        debug=False,
        pxy_ip="127.0.0.1",
        proxy_base_port=5561,
        be_ip="127.0.0.1",
        be_base_port=5563,
    ):
        """
        Constructor
        :param ctx: The raw ZMQ context to use.
        :param kp: The keypair to use, in the form {'be_key': '[path]', 'app_key': '[path]'}
        """
        self.ctx = ctx
        self.kp = kp
        self.pxy_ip = pxy_ip
        self.proxy_base_port = proxy_base_port
        self.be_ip = be_ip
        self.be_base_port = be_base_port
        threading.Thread.__init__(self)

    def run(self):
        context = self.ctx

        pub_public, pub_secret = zmq.auth.load_certificate(self.kp["be_key"])
        sub_public, sub_secret = zmq.auth.load_certificate(self.kp["app_key"])

        TCP_PXY_RTR = f"tcp://{self.pxy_ip}:{self.proxy_base_port+0}"
        TCP_BE_DLR = f"tcp://{self.be_ip}:{self.be_base_port+0}"

        frontend = context.socket(zmq.ROUTER)
        frontend.curve_publickey = pub_public
        frontend.curve_secretkey = pub_secret
        frontend.curve_server = True
        tprint(f"FAC--PXY: RouterProxy binding as Router to {TCP_PXY_RTR}")
        frontend.bind(TCP_PXY_RTR)

        backend = context.socket(zmq.DEALER)
        backend.curve_publickey = sub_public
        backend.curve_secretkey = sub_secret
        backend.curve_serverkey = pub_public
        tprint(f"PXY--BE: RouterProxy connecting as Dealer to {TCP_BE_DLR}")
        backend.connect(TCP_BE_DLR)

        try:
            zmq.proxy(frontend, backend)  # blocks
        except zmq.error.ContextTerminated:
            print("RouterProxy shutting down...")

        frontend.close()
        backend.close()


class PubProxyRuntime(threading.Thread):

    """
    Proxies between the proxy-publisher and the backend-subscriber sockets.
    """

    def __init__(
        self,
        ctx,
        kp,
        debug=False,
        pxy_ip="127.0.0.1",
        proxy_base_port=5561,
        be_ip="127.0.0.1",
        be_base_port=5563,
    ):
        """
        Constructor
        :param ctx: The raw ZMQ context to use.
        :param kp: The keypair to use, in the form {'be_key': '[path]', 'app_key': '[path]'}
        """
        self.ctx = ctx
        self.kp = kp
        self.pxy_ip = pxy_ip
        self.proxy_base_port = proxy_base_port
        self.be_ip = be_ip
        self.be_base_port = be_base_port
        threading.Thread.__init__(self)

    def run(self):
        context = self.ctx

        pub_public, pub_secret = zmq.auth.load_certificate(self.kp["be_key"])
        sub_public, sub_secret = zmq.auth.load_certificate(self.kp["app_key"])

        TCP_PXY_PUB = f"tcp://{self.pxy_ip}:{self.proxy_base_port+1}"
        TCP_BE_SUB = f"tcp://{self.be_ip}:{self.be_base_port+1}"

        frontend = context.socket(zmq.PUB)
        frontend.curve_publickey = pub_public
        frontend.curve_secretkey = pub_secret
        frontend.curve_server = True
        tprint(f"FAC--PXY: PubProxy binding as Publisher to {TCP_PXY_PUB}")
        frontend.bind(TCP_PXY_PUB)

        backend = context.socket(zmq.SUB)
        backend.curve_publickey = sub_public
        backend.curve_secretkey = sub_secret
        backend.curve_serverkey = pub_public
        backend.setsockopt(zmq.SUBSCRIBE, b"")
        tprint(f"PXY--BE: PubProxy connecting as Subscriber to {TCP_BE_SUB}")
        backend.connect(TCP_BE_SUB)

        try:
            zmq.proxy(frontend, backend)  # blocks
        except zmq.error.ContextTerminated:
            print("PubProxy shutting down...")

        frontend.close()
        backend.close()


def main():
    """
    Parses command line input and then runs PubProxy and RouterProxy.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        dest="debug",
        default=False,
        action="store_true",
        help="Enable debugging to console",
    )
    parser.add_argument(
        "--it",
        dest="proxy_base_port",
        type=int,
        default=5561,
        metavar="proxy_base_port",
        help="Interior proxy base port to bind to (->RTR<-, PUB, DLR, SUB)",
    )
    parser.add_argument(
        "--et",
        dest="be_base_port",
        type=int,
        default=5563,
        metavar="be_base_port",
        help="Base port of backend to connect to (RTR, PUB, ->DLR<-, SUB)",
    )
    parser.add_argument(
        "--ep",
        dest="be_ip",
        required=True,
        metavar="be_ip",
        help="IP of backend to connect to",
    )
    parser.add_argument(
        "--ip",
        dest="pxy_ip",
        required=True,
        metavar="pxy_ip",
        help="IP of internal proxy interface to bind to",
    )
    parser.add_argument(
        "--ak",
        dest="ak",
        required=True,
        metavar="appkey",
        help="The Curve public and private keys used by VMI apps",
    )
    parser.add_argument(
        "--bk",
        dest="bk",
        required=True,
        metavar="bekey",
        help="The Curve public and private keys for the backend",
    )
    args = parser.parse_args()
    print(f'{"#"*10}\nmain, starting Facilities with args: {args}\n{"#"*10}')

    if not os.path.isfile(args.ak) or not os.path.isfile(args.bk):
        print(f"ERROR: either {args.ak} or {args.bk} is is missing!")
        sys.exit()
    kp = {"be_key": args.bk, "app_key": args.ak}
    print(f"startup: keys OK")

    context = zmq.Context(io_threads=8)

    auth = ThreadAuthenticator(context)
    auth.start()
    auth.configure_curve(domain="*", location=zmq.auth.CURVE_ALLOW_ANY)

    proxy = RouterProxyRuntime(
        context,
        kp,
        debug=args.debug,
        pxy_ip=args.pxy_ip,
        proxy_base_port=args.proxy_base_port,
        be_ip=args.be_ip,
        be_base_port=args.be_base_port,
    )
    proxy.start()
    pubrelay = PubProxyRuntime(
        context,
        kp,
        debug=args.debug,
        pxy_ip=args.pxy_ip,
        proxy_base_port=args.proxy_base_port,
        be_ip=args.be_ip,
        be_base_port=args.be_base_port,
    )
    pubrelay.start()

    try:
        while True:
            tprintn(".")
            time.sleep(1)
    except KeyboardInterrupt:
        print("exiting...")
        auth.stop()
        context.term()


if __name__ == "__main__":
    main()
