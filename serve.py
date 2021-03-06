import pika, json

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='job-queue2', durable=True)

def getEngineDict(name, additionalString=""):
    return {"additionalString":additionalString, "compile":"true", "link":"https://github.com/OfekShochat/lc0-testing-zip/blob/main/lc0-master.zip?raw=true", "identifier":hash(name), "name":name}

message = {"job":{"tc":"0/10+0.1", "engine1":getEngineDict("lc0-bad"), "engine2":getEngineDict("lc0-regular")}}
body = json.dumps(message)

channel.basic_publish(exchange='', routing_key='job-queue2', body=str(body))
print(" [x] Sent '%s'" % body)
connection.close()