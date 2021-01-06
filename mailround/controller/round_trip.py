import datetime
import email.message
import email.utils
import io
import json
import logging
import threading
import urllib.parse
import urllib.request
import uuid

from config import settings
from controller.statuslog import StatusLog


class ContextFilter(logging.Filter):

    def filter(self, record):
        if type(record.threadName) is tuple:
            record.threadName = "->".join(record.threadName)

        return True


class RoundTrip(threading.Thread):

    def __init__(self, mailout, mailin, servernames, **kwargs):
        """
            This class manage the monitoring for a mailserver check
            :param mailin: Mail inbox Server must be a MailImapServer object or MailPopServerObject
            :type mailin: MailImapServer or MailPopServer
            :param mailout: Mail outgoing Server must be a MailSmtpServer object
            :param name: Tuple with the names of mailin and mailout
            :type name: tuple
        """
        super(RoundTrip, self).__init__(**kwargs)

        # E-Mail Inbox Server
        self._mail_in = mailin
        # E-Mail Out Server
        self._mail_out = mailout

        # Tupel with servernames
        self._name = servernames
        # UUID for Mail Tracking
        self.uuid = uuid.uuid4()
        # this variable becomes true when there is a suspicion that mails arrive late due to greylisting.
        self._graylisting = False
        # if this variable is true a notification will be triggerd after the full process
        self._error = False

        self._log_data = io.StringIO()
        self._log_handler = logging.StreamHandler(self._log_data)

        # error logging setup (Send in notifaction)
        self.log = self.setup_log()

        self.log.info("Test Connection between {} and {} ".format(*servernames))

        # Debug Output
        self.log.debug("")
        self.log.debug("OutServer")
        self.log.debug("-" * 20)
        self.log.debug("Host: {}".format(self._mail_out.host))
        self.log.debug("Port: {}".format(self._mail_out.port))
        self.log.debug("SSL: {}".format(self._mail_out.use_ssl))
        self.log.debug("User: {}".format(self._mail_out.credentials.username))
        self.log.debug("")
        self.log.debug("InServer")
        self.log.debug("-" * 20)
        self.log.debug("Host: {}".format(self._mail_in.host))
        self.log.debug("Port: {}".format(self._mail_in.port))
        self.log.debug("SSL: {}".format(self._mail_in.use_ssl))
        self.log.debug("User: {}".format(self._mail_in.credentials.username))

    def setup_log(self):

        log = logging.getLogger("mailround.controller.round_trip.{}".format("_".join(self._name)))

        formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')

        self._log_handler.setFormatter(formatter)
        self._log_handler.setLevel(logging.INFO)

        if hasattr(settings, "DEBUG"):
            if settings.DEBUG:
                self._log_handler.setLevel(logging.DEBUG)

        log.addHandler(self._log_handler)
        return log

    def run(self):

        StatusLog.get_instance().add_status(self.uuid.hex, self.name[0], self.name[1], "start")
        try:
            # Trigger Mail Sen
            StatusLog.get_instance().add_status(self.uuid.hex, self.name[0], self.name[1], "start_sendmail")
            self.sendmail()
            StatusLog.get_instance().add_status(self.uuid.hex, self.name[0], self.name[1], "end_sendmail")
        except Exception as e:
            self.log.exception(e)
            self._error = True
            self.log.error("Error by send E-Mail from {}".format(self._name[1]))

        if not self._error:
            try:
                StatusLog.get_instance().add_status(self.uuid.hex, self.name[0], self.name[1], "start_receive")
                self.receive()
                StatusLog.get_instance().add_status(self.uuid.hex, self.name[0], self.name[1], "end_receive")
            except Exception as e:
                self._error = True
                self.log.exception(e)
                self.log.error("Error by Recive E-Mail at Mailbox {} ".format(self._name[0]))

        if self._error:
            StatusLog.get_instance().add_status(self.uuid.hex, self.name[0], self.name[1], "error")
            if self._graylisting:
                StatusLog.get_instance().add_status(self.uuid.hex, self.name[0], self.name[1], "greylisting")
            self.notify()
        else:
            StatusLog.get_instance().add_status(self.uuid.hex, self.name[0], self.name[1], "success")
            self.log.info("SUCCESS between {} to {}".format(self.name[0], self.name[1]))
            self.log.removeHandler(self._log_handler)
            # log_contents = self._log_data.getvalue()
            self._log_data.close()

    def _gen_mail(self):
        self.log.debug("Generate E-Mail Message")
        msg = email.message.EmailMessage()

        msg["From"] = self._mail_out.email
        msg["To"] = self._mail_in.email
        msg['Subject'] = "[MailRound]"

        msg.add_header('X-Mail-Round', str(self.uuid.hex))
        msg.set_content("""This is a TestMail from MailRound.
Please do not delete this E-Mail Message. 
If MailRound works it will be deleted""")
        return msg

    def sendmail(self):
        self.log.debug("Try to send mail via {}".format(self._mail_out.host))
        conn = self._mail_out.get_connection()

        try:
            conn.send_message(self._gen_mail())
            self.log.info("E-Mail sucessfully send via {}".format(self._name[0]))
        except Exception as e:
            self.log.exception(e)
            pass
        finally:
            conn.quit()

    def _receive_idle(self, conn):
        ENDIDLE = False

        start_timestamp = datetime.datetime.now()
        conn.idle()
        self.log.debug("Set Mailbox to IDLE mode")
        while not ENDIDLE:
            try:
                # Wait for up to 30 seconds for an IDLE response
                responses = conn.idle_check(timeout=30)
                for response in responses:
                    # log.debug("Server sent:", response if response else "nothing")
                    if response[1].decode() == 'RECENT' and response[0] > 0:
                        ENDIDLE = True

                    if datetime.datetime.now() > start_timestamp + settings.MAX_MAIL_RECEIVE_TIME:
                        self.log.warn("Maximal Mailbox watchtime Reached. Terminate")
                        ENDIDLE = True
                        break

            except KeyboardInterrupt:
                break
        conn.idle_done()

    def _verify_mailround_mail(self, msg_id, data):
        if b"RFC822" not in data:
            return False
        bin_body = data[b"RFC822"]

        email_body = email.message_from_bytes(bin_body)
        mail_round_uuid = email_body.get_all("X-Mail-Round")

        if mail_round_uuid is None:
            return False

        if self.uuid.hex in mail_round_uuid:
            self.log.debug("Found Mail with same UUID")
            return True
        else:
            if len(mail_round_uuid) >= 1:
                self._graylisting = True

        return False

    def _delete_msg(self, conn, msg_id):
        conn.delete_messages(msg_id)
        conn.expunge(msg_id)

    def _seach_in_mailbox(self, conn):
        FOUND_MAIL_ROUND_TEST = False
        messages = conn.search()
        for message_id, data in conn.fetch(messages, ['RFC822']).items():

            if self._verify_mailround_mail(message_id, data):
                FOUND_MAIL_ROUND_TEST = True

                if hasattr(settings, "CLEANUP"):
                    self._delete_msg(conn, message_id)
                break
        return FOUND_MAIL_ROUND_TEST

    def receive(self):
        self.log.debug("Wait for E-Mail")

        start_timestamp = datetime.datetime.now()

        conn = self._mail_in.get_connection()
        conn.select_folder('INBOX')

        FOUND_MAIL_ROUND_TEST = self._seach_in_mailbox(conn)

        while not FOUND_MAIL_ROUND_TEST:
            self._receive_idle(conn)
            FOUND_MAIL_ROUND_TEST = self._seach_in_mailbox(conn)

            if datetime.datetime.now() > start_timestamp + settings.MAX_MAIL_RECEIVE_TIME:
                self.log.warn("Maximal Mailbox watchtime Reached. Terminate")
                self._error = True
                break

        if self._graylisting:
            self.log.warn("Found other E-Mails with Mail-Round Header. this is a note for active greylog")

        if self._error is False:
            self.log.info("E-Mail successfuly recived at {} from {}".format(self._name[1], self._name[0]))

        conn.logout()

    def notify(self):
        self.log.removeHandler(self._log_handler)
        log_contents = self._log_data.getvalue()
        self._log_data.close()

        body = {
            "text": """*Mailround*
Error between {}
```{}```""".format("->".join(self._name), log_contents),
        }

        req = urllib.request.Request(settings.WEBHOOK_URL)
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        jsondata = json.dumps(body)

        jsondataasbytes = jsondata.encode('utf-8')
        req.add_header('Content-Length', len(jsondataasbytes))

        response = urllib.request.urlopen(req, jsondataasbytes)

        # print("NOTIFY!!!!")
