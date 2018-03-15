CONFIG
====================
The file ~/.nebraska/config.json will be created on first running the script.
This json file contains the account ids and API keys for the banks the script
contacts.

The file format matches the lines below:
{
    "ids" : {
        "lloyds" : "USERID HERE"
    },
    "keys" : {
        "teller" : "API KEY HERE"
    }
}
End of file

CONFIG ERRORS
--------------------
Lloyds ID not in config:
  ~/.nebraska/config.json should contain your lloyds account id.
  Add "lloyds": "USERID HERE" to the set of ids.
  (Add "ids" : { "lloyds" : ... } if the ids entry is missing)

Teller API key not in config:
  ~/.nebraska/config.json should contain your teller.io API key.
  Add "teller": "API KEY HERE" to the set of keys.
  (Add "keys" : { "teller" : ... } if the keys entry is missing)
