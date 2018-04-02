#!/usr/bin/python3
"""
Main script for running the bank processor
"""
import argparse

from cli.sessionmode import SessionPrompt
from .session import Session


###########################################################
# PARSE ARGS
###########################################################
def parseargs():
    """Parse the cli arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cache', action='store_true',
                        help="Use the saved transactions file instead of "
                             "downloading from the web.")
    return parser.parse_args()


###########################################################
# MAIN
###########################################################
def main(args):
    """Run the main method"""
    session = Session()
    session.load(download=not args.cache)
    SessionPrompt(False, session).cmdloop()


###########################################################
# Start of script
###########################################################
if __name__ == '__main__':
    ARGS = parseargs()
    main(ARGS)
