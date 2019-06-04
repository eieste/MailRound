import smtplib
import imaplib
from imapclient import IMAPClient
import logging
import ssl


log = logging.getLogger("mailround.config")

class MailCredentials:

    def __init__(self, username, password):
        """
        Mailbox Credentials
        :param username: Mailbox username
        :param password: Mailbox password
        """
        self.username = username
        self.password = password


class MailServer:

    def __init__(self, host, port, use_ssl, email, credentials):
        """
        Basic Configuration for E-Mail Server ConnectionS
        :param host: Mail Server Hostname
        :param port: Mail Server Port
        :param use_ssl: Mail Server SSL Activated (bool)
        :param email:  Mail Server/Mailbox E-Mail address
        :param credentials: Mailbox Credentials
        """
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.email = email
        if isinstance(credentials, MailCredentials):
            self.credentials = credentials
        else:
            raise ValueError("Given credentials arent a MailCredential Object")


class MailPopServer(MailServer):

    def __init__(self, *args, **kwargs):
        raise NotImplemented("Pop Servers are currently not supported")


class MailImapServer(MailServer):

    def get_connection(self):
        """
        Establish Connection with settings defined in this object
        :return conn: ImapClient Connection
        """
        conn = IMAPClient(self.host, port=self.port, ssl=bool(self.use_ssl))
        conn.login(self.credentials.username, self.credentials.password)
        return conn


class MailSmtpServer(MailServer):

    def get_connection(self):
        """
        Establish connection with settings defined in this object
        :return conn: SMTP Server connection
        """
        if self.use_ssl:
            try:
                conn = smtplib.SMTP_SSL(self.host, self.port)
            except ssl.SSLError:
                conn = smtplib.SMTP(self.host, self.port)
        else:
            conn = smtplib.SMTP(self.host, self.port)

        conn.login(self.credentials.username, self.credentials.password)
        return conn
