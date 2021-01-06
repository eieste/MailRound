import logging
import os
import re
from datetime import timedelta
from os.path import join, dirname

from config.mail import MailSmtpServer, MailCredentials, MailImapServer, MailPopServer
from dotenv import load_dotenv

log = logging.getLogger("mailround.config")


class LoadEnvironment:
    ENV_PREFIX = "MAILROUND"

    def __init__(self, conf):
        self.REGEX = re.compile(
            r'MAILROUND_(?P<ServerType>IN_IMAP|IN_POP|OUT_SMTP)_(?P<Name>.*)_(?P<Setting>HOST|USERNAME|PASSWORD|USE_SSL|EMAIL|PORT)')

        dotenv_path = join(dirname(__file__), '../.env')
        load_dotenv(dotenv_path)
        self.conf = conf

        self.additional_config = {}

    def find_mail_round(self):
        settings = {}
        for env_key, env_value in os.environ.items():

            if self.check_prefix(env_key, self.ENV_PREFIX):
                settings[env_key] = env_value
        return settings

    def load(self):
        settings = self.find_with_prefix(os.environ, self.ENV_PREFIX)
        self.build_mailbox_config(settings)
        self.build_mailround_config(settings)

        if "MAILROUND_MAX_MAIL_RECEIVE_TIME" in settings:
            self.conf.MAX_MAIL_RECEIVE_TIME = timedelta(seconds=int(settings["MAILROUND_MAX_MAIL_RECEIVE_TIME"]))

        if "MAILROUND_WEBHOOK_URL" in settings:
            self.conf.WEBHOOK_URL = settings["MAILROUND_WEBHOOK_URL"]

        if "MAILROUND_DEBUG" in settings:
            self.conf.DEBUG = self.bool_parse(settings["MAILROUND_DEBUG"])

        if "MAILROUND_STATUS_LOG_PATH" in settings:
            self.conf.STATUS_LOG_PATH = settings["MAILROUND_STATUS_LOG_PATH"]

        if "MAILROUND_CLEANUP" in settings:
            self.conf.CLEANUP = self.bool_parse(settings["MAILROUND_CLEANUP"])

    def build_mailround_config(self, settings):

        if "MAILROUND_ROUND" in settings:

            pair_list = settings["MAILROUND_ROUND"].split(";")

            for pair in pair_list:
                send, to = pair.split(":")
                self.conf.MAIL_ROUND[send] = to

    def bool_parse(self, value):
        if str(value).lower() in [1, "true", "yes", "y", "ja", "j", "wahr", "w"]:
            return True
        return False

    def build_mailbox_config(self, oldsettings):

        settings = {}
        settings.update(self.find_with_prefix(oldsettings, "{}_IN_".format(self.ENV_PREFIX)))
        settings.update(self.find_with_prefix(oldsettings, "{}_OUT_".format(self.ENV_PREFIX)))

        mailboxes = {}

        def add(cat, server, setting, value):
            if cat not in mailboxes:
                mailboxes[cat] = {}
            if server not in mailboxes[cat]:
                mailboxes[cat][server] = {}

            mailboxes[cat][server][setting] = value

        for env_key, env_value in settings.items():
            res = self.REGEX.match(env_key)

            cat = "unknown"
            if "IMAP" in res["ServerType"] or "POP" in res["ServerType"]:
                cat = "in"

            if "SMTP" in res["ServerType"] or "OUT" in res["ServerType"]:
                cat = "out"

            add(cat, res["Name"], res["Setting"], env_value)

            if res["Setting"].lower() == "use_ssl":
                add(cat, res["Name"], res["Setting"], self.bool_parse(env_value))

            add(cat, res["Name"], "server_type", res["ServerType"])

        if "in" in mailboxes:
            self.add_in_mailboxes_to_config(mailboxes)

        if "out" in mailboxes:
            self.add_out_mailboxes_to_config(mailboxes)

    def add_out_mailboxes_to_config(self, mailboxes):
        for servername, server in mailboxes["out"].items():
            self.conf.MAIL_OUT_SERVER[servername] = MailSmtpServer(server["HOST"], server["PORT"], server["USE_SSL"],
                                                                   server["EMAIL"], MailCredentials(server["USERNAME"],
                                                                                                    server["PASSWORD"]))

    def add_in_mailboxes_to_config(self, mailboxes):

        for servername, server in mailboxes["in"].items():
            if "imap" in server["server_type"].lower():
                self.conf.MAIL_IN_SERVER[servername] = MailImapServer(server["HOST"], server["PORT"], server["USE_SSL"],
                                                                      server["EMAIL"],
                                                                      MailCredentials(server["USERNAME"],
                                                                                      server["PASSWORD"]))

            if "pop" in server["server_type"].lower():
                self.conf.MAIL_IN_SERVER[servername] = MailPopServer(server["HOST"], server["PORT"], server["USE_SSL"],
                                                                     server["EMAIL"],
                                                                     MailCredentials(server["USERNAME"],
                                                                                     server["PASSWORD"]))

    def find_with_prefix(self, settings, prefix):
        var_with_prefix = {}
        for env_key, env_value in settings.items():
            if self.check_prefix(env_key, prefix):
                var_with_prefix[env_key] = env_value
        return var_with_prefix

    def check_prefix(self, name, prefix):
        if name[:len(prefix)] == prefix:
            return True
        return False

    def remove_prefix(self, name, prefix):
        if name[len(prefix):len(prefix) + 1] == "_":
            return name[len(prefix) + 1:]
        return name[len(prefix):]
