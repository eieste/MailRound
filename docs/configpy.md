# Config py

```python


class Configuration:

    _ENV_PREFIX = "mailround_"

    """
        Interval in which the check should be carried out
    """
    CHECK_INTERVAL = timedelta(minutes=15)

    """ 
        List of Input Mailserver Objects like MailImapServer or MailPopServer
        The Dict key should be the servername
        eg:
        {
            "vps1": MailImapServer("mailin.example.com", 143, False, MailCredentials("test@example.com", "secret"))
        }
    """
    MAIL_IN_SERVER = {
    }

    """ 
        List of Output Mailserver Objects like MailSmtpServer
    
        {
            "vps2": MailSmtpServer("mailout.test.com", 143, False, MailCredentials("test@example.com", "secret"))
        }    
    """
    MAIL_OUT_SERVER = {
    }

    """
        Defines which Servers sends the Test Mail and with ones recive
        simpley key value pairs:
        {
            "vps1": "vps2"
        }
    """
    MAIL_ROUND = {
    }

    """ 
        Timeout to receive the test mail is to be maintained.
    """
    MAX_MAIL_RECEIVE_TIME = timedelta(seconds=10)

    """
        Trigger eg. Chat or FaaS if mailcheck is failing
    """
    WEBHOOK_URL = ""
    CLEANUP = True




```