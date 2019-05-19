# MailRound
![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/eieste/mailround.svg)
[![Build Status](https://travis-ci.com/eieste/MailRound.svg?branch=develop)](https://travis-ci.com/eieste/MailRound)
[![PyPI version](https://badge.fury.io/py/mailround.svg)](https://badge.fury.io/py/mailround)
![GitHub release](https://img.shields.io/github/release/eieste/mailround.svg)
![GitHub tag (latest SemVer)](https://img.shields.io/github/tag/eieste/mailround.svg)

Simple tool to check the sending and receiving of e-mails.

You can use this tool to Check functionality of Mailservers (in and outgoing)
If an error occurs during a connection check, the tool will inform you with the help of a webhook.

You can define Multiple Connections and which server send or recive the E-Mail.
You can excatly define which server Send the test email and which should be received

Its also possible to use this tool on production Mailboxes. (The test E-mails are Automaticly deleted)


Use the docker-compose file to test this Application fast.

```dockerfile
version: "3.2"

services:
  mailround:
    image: eieste/mailround:develop
    environment:
      MAILROUND_IN_IMAP_vps1_HOST: "examplemailserver.com"
      MAILROUND_IN_IMAP_vps1_PORT: 143
      MAILROUND_IN_IMAP_vps1_USE_SSL: true
      MAILROUND_IN_IMAP_vps1_USERNAME: "accuontusername"
      MAILROUND_IN_IMAP_vps1_PASSWORD: "randompassword"
      MAILROUND_IN_IMAP_vps1_EMAIL: "test@example.com"

      MAILROUND_OUT_SMTP_vps2_HOST: "examplemailserver.com"
      MAILROUND_OUT_SMTP_vps2_PORT: 143
      MAILROUND_OUT_SMTP_vps2_USE_SSL: true
      MAILROUND_OUT_SMTP_vps2_USERNAME: "accuontusername"
      MAILROUND_OUT_SMTP_vps2_PASSWORD: "randompassword"
      MAILROUND_OUT_SMTP_vps2_EMAIL: "test@example.com"

      MAILROUND_MAX_MAIL_RECEIVE_TIME: 60
      MAILROUND_ROUND: vps2:vps1
      MAILROUND_WEBHOOK_URL: "<FAAS>or<ROCKETCHAT> URL"

```

For more Assistance use my [Documentation](https://github.com/eieste/MailRound/blob/develop/docs/overview.md)