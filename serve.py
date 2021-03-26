import pika
import json
import argparse

parser = argparse.ArgumentParser(description="the lc0 testing framework")
parser.add_argument("--time-control", "-tc", help="time control for the test")
parser.add_argument("--game-number", "-gn", help="number of tasks to spawn for the test")
parser.add_argument("--pubkey", "-pk", help="filename to rsa public key")

connection = pika.BlockingConnection(
    pika.ConnectionParameters(credentials=pika.credentials.PlainCredentials("username", "password"), host='localhost', heartbeat=600, blocked_connection_timeout=500))
channel = connection.channel()

channel.queue_declare(queue='lc0-jobs', durable=True)

def getEngineDict(name, link, additionalString=""):
    return {"additionalString":additionalString, "compile":"true", "link":link, "identifier":hash(name) + hash(link), "name":name}

message = {"job":{"tc":"0/10+0.1", "engine1":getEngineDict("lc0-bad", "https://github.com/OfekShochat/lc0"), "engine2":getEngineDict("lc0-regular", "https://github.com/OfekShochat/lc0")}}
body = json.dumps(message)

channel.basic_publish(exchange='', routing_key='lc0-jobs', body=str(body),
                     properties=pika.BasicProperties
                        (
                            delivery_mode = 2, # make message persistent
                        ))
print(" [x] Sent '%s'" % body)