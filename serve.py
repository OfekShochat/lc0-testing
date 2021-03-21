from b_rabbit import BRabbit
import json

def response(body):
    open("pgns.pgn", "a+").write(body.decode() + "\n\n")

def getEngineDict(name, additionalString=""):
    return {"additionalString":additionalString, "compile":"true", "link":"https://github.com/OfekShochat/lc0-testing-zip/blob/main/lc0-master.zip?raw=true", "identifier":hash(name), "name":name}

message = {"job":{"tc":"0/10+0.1", "engine1":getEngineDict("lc0-bad"), "engine2":getEngineDict("lc0-regular")}}
body = json.dumps(message)

rabbit = BRabbit(host='localhost', port=5672)

taskRequesterSynchron = rabbit.TaskRequesterSynchron(b_rabbit=rabbit,
                                                     executor_name='WebsiteAutomationService',
                                                     routing_key='WebsiteAutomationService.createNewGeofence',
                                                     response_listener=response)

taskRequesterSynchron.request_task(body)

print(" [x] Sent '%s'" % body)
rabbit.close_connection()