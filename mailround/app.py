import argparse
from config import settings
from controller.round_trip import RoundTrip
import threading
import logging
import io
from controller.statuslog import StatusLog
from datetime import datetime
import time


logging.basicConfig(level=logging.INFO)

log = logging.getLogger("mailround.app")


class Command:

    def __init__(self, *args, **kwargs):
        self.arg = argparse.ArgumentParser()

    def arguments(self, parser):
        parser.add_argument("-v", "--verbose", help="increase output verbosity",
                            action="store_true")
        parser.add_argument("--full-clean", help="Remove all MailRound E-Mails from all Mailboxes", action="store_true")
        parser.add_argument("--no-cleanup", help="Do not Delete testmail", action="store_true")

    def handle(self, options):
        statuslog = StatusLog.get_instance()

        log.info("Start Mail-Round")

        if options.verbose:
            logging.basicConfig(level=logging.DEBUG)

            logger = logging.getLogger('imaplib.imapclient')
            logger.setLevel(logging.INFO)
            logger = logging.getLogger('imapclient.imaplib')
            logger.setLevel(logging.INFO)

        if options.no_cleanup:
            setattr(settings, "CLEANUP", False)

        if options.full_clean:
            for server_name, server_config in settings.MAIL_IN_SERVER.items():
                self.mailbox_cleanup(server_config)
                statuslog.stop()
            exit(0)

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
        log.debug("Thread for {} {} ".format(outname, inname))
        if "{}{}".format(outname, inname) in mailround_thread_store:
            t = mailround_thread_store["{}{}".format(outname, inname)]
            if not t._is_stopped:
                log.debug("Stop Thread {}{}".format(outname, inname))
                t.join(2)

        log.debug("Create new Thread {}{}".format(outname, inname))
        mailround_thread_store["{}{}".format(outname, inname)] = RoundTrip(settings.MAIL_OUT_SERVER[outname], settings.MAIL_IN_SERVER[inname], (outname, inname), name="rt-{}{}".format(outname, inname))
        return mailround_thread_store["{}{}".format(outname, inname)]


    def mailbox_cleanup(self, server_config):
        conn = server_config.get_connection()
        conn.select_folder("INBOX")
        messages = conn.search()
        for message_id, data in conn.fetch(messages, ['RFC822']).items():
            conn.delete_messages(message_id)
            conn.expunge(message_id)
        conn.logout()

if __name__ != "__name__":

    parser = argparse.ArgumentParser()

    cmd = Command()
    cmd.arguments(parser)

    options = parser.parse_args()

    cmd.handle(options)
