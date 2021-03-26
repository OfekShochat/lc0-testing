import pika
import json
import argparse

parser = argparse.ArgumentParser(description="the lc0 testing framework")
parser.add_argument("--time-control", "-tc", help="time control for the test", type=str)
parser.add_argument("--game-number", "-gn", help="number of tasks to spawn for the test", type=int)
parser.add_argument("--username", "-un", help="username for credentials", type=str)
parser.add_argument("--password", "-pw", help="password for credentials", type=str)

args = parser.parse_args()

connection = pika.BlockingConnection(
    pika.ConnectionParameters(credentials=pika.credentials.PlainCredentials(args.username, args.password), host='localhost', heartbeat=600, blocked_connection_timeout=500))
channel = connection.channel()

channel.queue_declare(queue='lc0-jobs', durable=True)

def getEngineDict(name, link, compile="true", additionalString=""):
    return {"additionalString":additionalString, "compile":compile, "link":link, "identifier":hash(name) + hash(link), "name":name}

message = {"job":{"tc":"0/10+0.1", "engine1":getEngineDict("lc0-bad", "https://github.com/OfekShochat/lc0"), "engine2":getEngineDict("lc0-regular", "https://github.com/OfekShochat/lc0")}}
body = json.dumps(message)

channel.basic_publish(exchange='', routing_key='lc0-jobs', body=str(body),
                     properties=pika.BasicProperties
                        (
                            delivery_mode = 2, # make message persistent
                        ))
print(" [x] Sent '%s'" % body)