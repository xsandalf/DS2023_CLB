#!/usr/bin/env python3
# first app = package name (directory app/),
# second app = Flask class name (variable defined in __init__.py)
from app import app
from flask import render_template, request
from random import randint

# Register callbacks with URLs
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    # Payload template to simulate workload (read: python files) that client would input
    # time.sleep emulates a computing heavy file that requires random_int seconds to execute
    # returns a sum of two integers to signify execution has ended
    payload_template = """
    #!/usr/bin/env python3\n
    import time\n
    \n
    time.sleep({random_int})\n
    return {random_int2} + {random_int3}
    """.format(random_int=randint(10,60), random_int2=randint(1,10), random_int3=randint(1,10))
    payload = ""

    # Placeholder payloads
    payloads = [{"hash" : "0sdkfosr4ij39rjfof93j", "result" : "6"},
                {"hash" : "dkfmksdnfinrei4ni3ijf", "result" : "pending"},
                {"hash" : "odsokfndfinsiednfsen3", "result" : "pending"}]

    if request.method == "POST":
        if request.form.get("generate_payload") == "Generate Payload":
            #print("GET FUCKED NERD", flush=True)
            payload = payload_template
            return render_template("index.html", generated_payload=payload, payloads=payloads)
        elif request.form.get("send_payload") == "Send Payload":
            print("GET FUCKED NERD", flush=True)
            print(payload, flush=True)
            if len(payload) > 0:
                print("GET FUCKED NERD", flush=True)
                print(hash(payload), flush=True)
                return render_template("index.html", generated_payload=payload, payloads=payloads)

    # Return index.html with additional paremeters
    return render_template("index.html", generated_payload=payload, payloads=payloads)
