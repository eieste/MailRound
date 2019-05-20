# Statuslog


MailRound can also Provide a Statuslog


The Statuslog is saved as msgpack. and contains the json equivalent of:


```json

{
  "version": "1.0.0",
  "signature": "<SHAHASH>",
  "config": {
    "server": [
        {
          "server_type": IMAP|POP|SMTP,
          "host": "",
          "port": "",
          "use_ssl": "",
          "server_name",
          "valid_at": 0123456789
        }
    ],
    "rounds": [
      {
        "in": "name",
        "out": "name",
        "timestamp": 0123456789
      } 
    ]
  },
  "status": [
    {
      "in": "inanme",
      "out": "outname",
      "timestamp": 0123456789.
      "status": "status",
      "meta": {
      
      }
    }
  ]
}





```