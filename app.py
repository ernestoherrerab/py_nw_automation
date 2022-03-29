#! /usr/bin/env python
"""
Executes the main app
"""
import argparse
import sys
sys.dont_write_bytecode = True
from decouple import config
from waitress import serve
from flask import Flask 
from network_automation import app

def parse_args():
    """
    Process the command line arguments
    """
    parser = argparse.ArgumentParser(
        description = "Type -e To select if it is a development or production environment\n"
                        " The options are dev and prod"
        )
    required_argument = parser.add_argument_group("Required Arguments")
    required_argument.add_argument(
        "-e", "--environment", help = "environment", default="stdout", required=True
    )
    args = parser.parse_args()
    return args


### SERVER ENVIRONMENTAL VARIABLES ###
FLASK_SERVER = config("FLASK_SERVER")
DEBUG_MODE = eval(config("FLASK_DEBUG_MODE"))
SERVER_PORT = int(config("FLASK_SERVER_PORT"))

if __name__ == "__main__":
    args = parse_args()
    if args.environment == "dev":
        ### EXECUTE THE APP ###
        app.run(debug=DEBUG_MODE, host=FLASK_SERVER, port=SERVER_PORT)
    elif args.environment == "prod":
        serve(app, host=FLASK_SERVER, port=SERVER_PORT)
