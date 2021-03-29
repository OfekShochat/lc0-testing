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
    pika.ConnectionParameters(credentials=pika.credentials.PlainCredentials(args.username, args.password), host='192.168.140.118', heartbeat=600, blocked_connection_timeout=500))
channel = connection.channel()

channel.queue_declare(queue='lc0-jobs', durable=True)

def getEngineDict(name, link, compile="true", additionalString="", network="default"):
    return {"additionalString":additionalString, "compile":compile, "link":link, "identifier":hash(name) + hash(link), "name":name, "network":network}

message = {"test-identifier":hash(id("lc0-testing-is-the-best")), "job":{"tc":args.time_control, "engine1":getEngineDict("lc0", "https://github.com/LeelaChessZero/lc0", network="https://training.lczero.org/get_network?sha=ac779e83b250debf04c4406835159e46f9a64b99003fc14702608735da4b496a"), "engine2":getEngineDict("lc0-regular", "https://github.com/LeelaChessZero/lc0")}}
for i in range(args.game_number):
    if i % 2 == 1:
        b = message["job"].copy()
        bk = list(b.keys())
        bv = list(b.values())

        ai = bk.index("engine1")
        bi = bk.index("engine2")
        bk[ai], bk[bi] = bk[bi], bk[ai]
        b = dict(zip(bk, bv))
        body = message.copy()
        body["job"] = b
    else:
        body = message
    
    print(" [x] Sent '%s'" % body)
    channel.basic_publish(exchange='', routing_key='lc0-jobs', body=json.dumps(body),
                            properties=pika.BasicProperties
                                (
                                    delivery_mode = 2, # make message persistent
                                ))