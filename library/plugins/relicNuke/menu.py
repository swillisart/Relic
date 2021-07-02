import nuke
import nukescripts
import numpy as np

def assetDropCallback(mimeType, payload):
    if payload.endswith(".pyw"):
        with open(payload, "rb") as fp:
            script = fp.read()
            exec(script, None, {"pathd": payload})
        return True

    elif ".pyw" in payload:
        print(payload)
        items = payload.split()
        print(items)
        payload = items[0]
        with open(payload, "rb") as fp:
            script = fp.read()
            print(script)
            exec(script, None, {"ids": items[2:], "category": items[1], "pathd": payload})

        return True
    return None


if nuke.GUI:
    nukescripts.addDropDataCallback(assetDropCallback)
