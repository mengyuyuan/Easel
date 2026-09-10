"""Print the primary device id from the easel gateway state DB."""
import os
import sqlite3

path = os.path.expanduser("~/.openclaw-easel/state/openclaw.sqlite")
con = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
row = con.execute(
    "SELECT device_id FROM device_identities WHERE identity_key = 'primary'"
).fetchone()
print(row[0] if row else "")
