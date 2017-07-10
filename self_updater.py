import os
import sys
import time

import git

def check_for_updates():
    """ Clones master branch of repo from git """
    pass

def restart(logger, seconds_before_restart=5):
    """ Waits a determined amount of time and then restarts
        this program.
    """
    pre_wait_message = 'event loop has stopped... waiting {sec} seconds before restart'
    restarting_message = 'restarting bot...'

    logger.debug(pre_wait_message.format(sec=seconds_before_restart))
    time.sleep(seconds_before_restart)
    logger.debug(restarting_message)

    python = sys.executable
    os.execl(python, python, *sys.argv)