import argparse
from config import settings
from controller.round_trip import RoundTrip
import threading
import logging
import io
from datetime import datetime
import time


log = logging.getLogger("mailround.app")


class Command:

    def __init__(self, *args, **kwargs):
        self.arg = argparse.ArgumentParser()

    def arguments(self, parser):
        parser.add_argument("-v", "--verbose", help="increase output verbosity",
                            action="store_true")

        parser.add_argument("--no-cleanup", help="Do not Delete testmail", action="store_true")


    def handle(self, options):

        log.info("Start Mail-Round")

        if options.verbose:
            logging.basicConfig(level=logging.DEBUG)

            logger = logging.getLogger('imaplib.imapclient')
            logger.setLevel(logging.INFO)
            logger = logging.getLogger('imapclient.imaplib')
            logger.setLevel(logging.INFO)

        if options.no_cleanup:
            setattr(settings, "CLEANUP", False)


        mailround_thread_store = {}

        if len(settings.MAIL_ROUND.items()) <= 0:
            raise EnvironmentError("Nothing todo. No configuration provided")

        log.info("Start Mail Check")
        last_check = datetime.fromtimestamp(0)
        while True:

            if last_check < datetime.now()-settings.CHECK_INTERVAL:
                last_check = datetime.now()

                for outname, inname in settings.MAIL_ROUND.items():
                    rt = self.get_thread(outname, inname, mailround_thread_store)
                    rt.start()
            time.sleep(1)

    def get_thread(self, outname, inname, mailround_thread_store):
        log.info("Thread for {} {} ".format(outname, inname))
        if "{}{}".format(outname, inname) in mailround_thread_store:
            t = mailround_thread_store["{}{}".format(outname, inname)]
            if not t._is_stopped:
                log.info("Stop Thread {}{}".format(outname, inname))
                t.join(2)

        log.info("Create new Thread {}{}".format(outname, inname))
        mailround_thread_store["{}{}".format(outname, inname)] = RoundTrip(settings.MAIL_OUT_SERVER[outname], settings.MAIL_IN_SERVER[inname], (outname, inname), name="rt-{}{}".format(outname, inname))
        return mailround_thread_store["{}{}".format(outname, inname)]




if __name__ != "__name__":

    parser = argparse.ArgumentParser()

    cmd = Command()
    cmd.arguments(parser)

    options = parser.parse_args()

    cmd.handle(options)
