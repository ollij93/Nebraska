"""
Private common utilities for the banking package
"""
import cmd
import io
import json
import os
import pydoc
import sys

NEBRASKA_DIR = os.path.join(os.path.expanduser("~"), ".nebraska")

KNOWN_DESCS_FILE = os.path.join(NEBRASKA_DIR, "known_descriptions.json")
CONFIG_FILE = os.path.join(NEBRASKA_DIR, "config.json")
CACHE_FILE = os.path.join(NEBRASKA_DIR, "cache.json")

class BaseCmd(cmd.Cmd):
    """Base class for commands available on all prompts"""
    def __init__(self, paging_on):
        super().__init__()
        self.paging_on = paging_on
        self.out = None
        if paging_on:
            self.turn_paging_on()
        else:
            self.turn_paging_off()

    def precmd(self, line):
        self.start_pager()
        return line

    def postcmd(self, stop, line):
        self.flush_pager()
        return stop

    def turn_paging_on(self):
        """Turn on paging"""
        self.paging_on = True

    def turn_paging_off(self):
        """Turn off paging"""
        self.paging_on = False
        sys.stdout = sys.__stdout__

    def start_pager(self):
        """Start paging"""
        if self.paging_on:
            self.out = io.StringIO()
            sys.stdout = self.out

    def flush_pager(self):
        """Flush the pager"""
        sys.stdout = sys.__stdout__
        if self.paging_on and self.out is not None:
            pydoc.pager(self.out.getvalue())
        self.out = None

    def do_paging_off(self, _):
        """Turn paging off"""
        self.turn_paging_off()

    def do_paging_on(self, _):
        """Turn paging on"""
        self.turn_paging_on()

    def do_EOF(self, _): # pylint: disable=C0103
        """Handle EOF (AKA ctrl-d)."""
        print("")
        return self.do_exit(None)

    def do_exit(self, _): # pylint: disable=R0201
        """Exit this submode."""
        return True

    def _option_selection(self, options):
        """Have the user select one of the given options"""
        for index, option in enumerate(options):
            print("({:>3}) {}".format(index, option))
        self.flush_pager()

        option = None
        while True:
            try:
                choice = input("Choose (range 0:{}): ".format(len(options) - 1))
            except EOFError:
                print("")
                break
            # Exit option selection on empty input
            if not choice:
                break
            try:
                index = int(choice)
                option = options[index]
            except (ValueError, IndexError):
                pass
            else:
                break
        return option


class BasePrompt(BaseCmd):
    """
    Abstract class for all prompts to be based upon to handle common commands
    to all modes
    """
    def __init__(self, paging_on, known_descriptions, accounts):
        super().__init__(paging_on)
        self.known_descriptions = known_descriptions
        self.accounts = accounts

    def do_save(self, _):
        """Save the current state of the accounts to the users cache"""
        with open(CACHE_FILE, "w") as outfile:
            json.dump({"accounts": [account.to_dict() for account in self.accounts]},
                      outfile,
                      indent=4,
                      sort_keys=True)
            print("cache created")
