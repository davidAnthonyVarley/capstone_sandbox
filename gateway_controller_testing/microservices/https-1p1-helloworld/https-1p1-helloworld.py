from flask import Flask
import sys
import argparse

def parse_arguments():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="A simple HTTP/3 server")
    
    # Define --cert and --key arguments, which will be passed from K8s
    parser.add_argument(
        "--cert",
        type=str,
        required=True,
        help="Path to the TLS certificate file (e.g., /certs/tls.crt)"
    )
    parser.add_argument(
        "--key",
        type=str,
        required=True,
        help="Path to the TLS private key file (e.g., /certs/tls.key)"
    )
    # Add other arguments if necessary (like --host or --port)
    parser.add_argument(
        "--port",
        type=int,
        default=30001,
        help="Port to listen on"
    )

    # Parse args, excluding the script name itself (sys.argv[0])
    # Note: When run via K8s args, you may receive the script name, but argparse handles this well.
    return parser.parse_args(sys.argv[1:])

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello world, from py HTTPS 1.1 server", 200

#Local development
path_to_certs = "C:\\Users\\david\\capstone_sandbox\\gateway_controller_testing\\certs"
cert = path_to_certs + "\\cert.pem"
key = path_to_certs + "\\key.pem"

#for k8s cluster
args = parse_arguments()
cert = args.cert
key = args.key


app.run(
    host="0.0.0.0", 
    port=30001,
    ssl_context=(cert, key)
)

