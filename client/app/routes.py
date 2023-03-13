#!/usr/bin/env python3
# first app = package name (directory app/),
# second app = Flask class name (variable defined in __init__.py)
from app import app
from flask import render_template, request
from random import randint

# Bad coding practice, "dirty hack" :D
payload = ""
payloads = []

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
    
    # Tell interpreter where to find payload and payloads
    global payload
    global payloads

    # POST-request means a button was pressed, figure out which one and either generate a payload or
    # send the payload forward to be executed in another container
    if request.method == "POST":
        if request.form.get("generate_payload") == "Generate Payload":
            # Get new payload
            payload = payload_template
            # Re-render page and show the payload
            return render_template("index.html", generated_payload=payload, payloads=payloads)
        elif request.form.get("send_payload") == "Send Payload":
            # Ignore clicks if payload isn't created
            if len(payload) > 0:
                print(hash(payload), flush=True)
                # Store payload, its hash, and current state to a dictionary
                payloads.append({"hash" : str(hash(payload)), "payload" : payload, "result" : "executing"})
                # Empty payload so user cannot flood the system with the same payload
                payload = ""
                # Re-render page and show the payload in the execution table
                return render_template("index.html", generated_payload=payload, payloads=payloads)
    else:
        payload = ""
        payloads = []

    # Return index.html with additional paremeters
    return render_template("index.html", generated_payload=payload, payloads=payloads)
