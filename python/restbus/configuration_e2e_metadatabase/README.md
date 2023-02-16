# Sample E2E configuration

This configuration uses a conventional `.dbc` signal database and pairs it with a meta database `.meta.json`. All _E2E_ information is stored in the meta database file.

Note that the meta database pairing is determined on the file name: `<signal database>.meta.json`.

Link to files in configuration:

- [can/test.dbc](can/test.dbc), DBC signal database.
- [can/test.dbc.meta.json](can/test.dbc.meta.json), meta database.
- [interfaces.json](interfaces.json), as broker configuration file.

Run this configuration as a _rest bus_:

    python restbus.py --configure configuration_e2e_metadatabase --namespace myecu --verbose
