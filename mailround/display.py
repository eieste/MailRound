import json
import msgpack
from config import settings
import time
#
#
# with open(settings.STATUS_LOG_PATH, "rb+") as fobj:
#     foo = msgpack.unpack(fobj, raw=False)
#     print(foo)
    #print(fobj.read())
    #dat = msgpack.unpack(fobj, raw=False)
    #print(json.dumps(dat, indent=4))

# return msgpack.unpack(fobj, raw=False)



data = {
    "test": []
}


def a():
    with open("a.bin", "ab+") as fobj:
        fobj.seek(0)
        try:
            foo = msgpack.unpack(fobj, raw=False)
        except Exception as e:
            foo = {"test":[]}
        fobj.truncate(0)
        fobj.seek(0)
        print(foo)
        foo["test"].append(str(time.time()))
        msgpack.pack(foo, fobj)

a()