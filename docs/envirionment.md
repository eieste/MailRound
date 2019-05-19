# Use Environment Variables

All Environment variables have the Prefix MAILROUND_`



## Mail Server Configuration

To configure multiple MailServers you can create a dynamic amount of environment variables.
This environment variables must be like:


`MAILROUND_IN_<Type>_<Name>_<Setting>`

Available Types:
 * `ÌMAP`
 * `POP`
 
The Name part is defined by you. It is useful when you use provider name, oder server hostname

Available Settings:
 * `HOST`
 * `PORT`
 * `USE_SSL`
 * `USERNAME`
 * `PASSWORD`
 * `EMAIL`
 
**Difference between USERNAME and EMAIL** <br>
Username is used at authentification on mailserver
E-Mail descripes the mail adress of this mailbox. (used to send the test E-Mail to it)

### Example

IMAP Mailbox Example
```
    MAILROUND_IN_IMAP_vps1_HOST="examplemailserver.com"
    MAILROUND_IN_IMAP_vps1_PORT=143
    MAILROUND_IN_IMAP_vps1_USE_SSL=true
    MAILROUND_IN_IMAP_vps1_USERNAME="accuontusername"
    MAILROUND_IN_IMAP_vps1_PASSWORD="randompassword"
    MAILROUND_IN_IMAP_vps1_EMAIL="test@example.com"
```

POP Mailbox Example
```
    MAILROUND_IN_POP_vps2_HOST="ahotherexamplemailserver.com"
    MAILROUND_IN_POP_vps2_PORT=143
    MAILROUND_IN_POP_vps2_USE_SSL=true
    MAILROUND_IN_POP_vps2_USERNAME="accuontusername"
    MAILROUND_IN_POP_vps2_PASSWORD="randompassword"
    MAILROUND_IN_POP_vps2_EMAIL="another@example.com"
```