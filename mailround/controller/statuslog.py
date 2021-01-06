import hashlib
import json
import logging
import os
import threading
import time
from queue import Queue

import msgpack
from config import settings
from config.mail import MailSmtpServer, MailPopServer, MailImapServer
from jsonschema import validate

log = logging.getLogger("controller.statuslog")


class StatusLog:
    instance = False

    @staticmethod
    def get_instance():
        if not StatusLog.instance:
            StatusLog.instance = StatusLog()
        return StatusLog.instance

    def __init__(self):
        self.queue = Queue()
        self._stop = False
        self._writer_thread = StatusWriter(self, name="statuswriter")
        self._writer_thread.start()

    def __del__(self):
        self._writer_thread.join(12)

    def stop(self):
        self._stop = True
        self._writer_thread.join(1)

    def add_status(self, group, outname, inname, status, **kwargs):
        options = {
            "group": group,
            "out": outname,
            "in": inname,
            "status": status,
            "timestamp": time.time(),
        }
        options.update(kwargs)
        self.queue.put(options)

    def get_queue(self):
        return self.queue


class StatusWriter(threading.Thread):

    def __init__(self, statuslog, *args, **kwargs):
        super(StatusWriter, self).__init__(*args, **kwargs)
        self.statuslog = statuslog

    def get_queue(self):
        return self.statuslog.get_queue()

    def run(self):

        while not self.statuslog._stop:

            if not self.get_queue().empty():
                with open(settings.STATUS_LOG_PATH, "ab+") as fobj:
                    fobj.seek(0)

                    if len(fobj.read()) > 0:
                        data = self.read_statuslog(fobj)
                    else:
                        data = {}

                    if self.integrity_check(data):
                        if data == {}:
                            data["version"] = "1.0.0"

                        data = self.cleanup_statuslog(data)
                        data = self.update_settings_at_statuslog(data)
                        data = self.add_status_to_statuslog(data)
                        self.write_statuslog(fobj, data)
                    else:
                        log.error("Corrupt File")
            time.sleep(1)

    def integrity_check(self, data):
        log.debug("Check Integrity")
        try:
            if not bool(data):
                log.warn("New File detected")
                return True
            else:
                if not data["version"] == "1.0.0":
                    log.error("Wrong File Version {}".format(data["version"]))
                    return False
                m = hashlib.sha256()
                m.update(msgpack.packb({"status": data["status"], "config": data["config"]}))
                if not data["signature"] == m.hexdigest():
                    log.error("Wrong Signature")
                    return False

                path = os.getcwd()

                with open("{}/controller/statuslog.schema".format(path), "r") as fobj:
                    schema = json.load(fobj)
                if validate(instance=data, schema=schema):
                    log.error("Wrong Schema")
                    return False
                log.debug("Integrity looks fine")
                return True

        except Exception as e:
            log.exception(e)
            log.error("Invalid Statuslog file")
        return False

    def read_statuslog(self, fobj):
        fobj.seek(0)
        return msgpack.unpack(fobj, raw=False)

    def write_statuslog(self, fobj, data):
        m = hashlib.sha256()
        m.update(msgpack.packb({"status": data["status"], "config": data["config"]}))
        data["signature"] = m.hexdigest()

        fobj.truncate(0)
        fobj.seek(0)

        msgpack.pack(data, fobj, use_bin_type=True)

    def cleanup_statuslog(self, data):
        # ToDo cleanup Old Configs, Old Rounds and old Status Messages
        return data

    def update_settings_at_statuslog(self, data):
        if "config" not in data:
            data["config"] = {}

        if "server" not in data:
            data["config"]["server"] = []

        if "status" not in data:
            data["config"]["round"] = []

        for server_name, server_config in settings.MAIL_IN_SERVER.items():
            data["config"]["server"] = data["config"]["server"] + self._add_server_to_config(server_name, server_config)

        for server_name, server_config in settings.MAIL_OUT_SERVER.items():
            data["config"]["server"] = data["config"]["server"] + self._add_server_to_config(server_name, server_config)

        data["config"]["round"] = [{"in": inname, "out": outname, "timestamp": time.time()} for outname, inname in
                                   settings.MAIL_ROUND.items()]
        return data

    def _add_server_to_config(self, server_name, server_config):
        result = []
        FOUND_SAME_ENTRY = False
        SERVER_TYPE = "UNKNOWN"

        if isinstance(server_config, MailImapServer):
            SERVER_TYPE = "IMAP"

        if isinstance(server_config, MailPopServer):
            SERVER_TYPE = "POP"

        if isinstance(server_config, MailSmtpServer):
            SERVER_TYPE = "SMTP"

        for config in result:
            if config["host"] == server_config.host and \
                    config["port"] == server_config.port and \
                    config["server_name"] == server_name and \
                    config["use_ssl"] == server_config.use_ssl:

                if isinstance(server_config, MailImapServer) and \
                        config["server_type"] == "IMAP":
                    FOUND_SAME_ENTRY = True

                if isinstance(server_config, MailPopServer) and \
                        config["server_type"] == "POP":
                    FOUND_SAME_ENTRY = True

                if isinstance(server_config, MailSmtpServer) and \
                        config["server_type"] == "SMTP":
                    FOUND_SAME_ENTRY = True

        if not FOUND_SAME_ENTRY:
            result.append({
                "server_type": SERVER_TYPE,
                "host": server_config.host,
                "port": int(server_config.port),
                "use_ssl": bool(server_config.use_ssl),
                "server_name": server_name,
                "valid_at": time.time()
            })
        return result

    def add_status_to_statuslog(self, data):

        if "status" not in data:
            data["status"] = []

        while not self.get_queue().empty():

            item = self.get_queue().get(True, 10)
            if item is not None:
                data["status"].append(item)
            else:
                break
        return data
