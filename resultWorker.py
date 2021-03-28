from pgn_parser import parser, pgn
import pika
import argparse
import json
import os

if not os.path.isdir("results"): os.mkdir("results")

parser = argparse.ArgumentParser(description="the lc0 testing framework resultsWorker")
parser.add_argument("--username", "-un", help="username for credentials", type=str)
parser.add_argument("--password", "-pw", help="password for credentials", type=str)

args = parser.parse_args()

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(credentials=pika.credentials.PlainCredentials(args.username, args.password), host='localhost', heartbeat=600, blocked_connection_timeout=500))
    channel = connection.channel()

    channel.queue_declare(queue='lc0-submit', durable=True)

    def callback(ch, method, properties, body):
        print("  [x] Received result")
        body = json.loads(body.decode())
        for i in body["result"].split("\n"):
            if i.startswith("[White"):
                print("  [x] " + i[1:-1])
            elif i.startswith("[Black"):
                print("  [x] " + i[1:-1])
            elif i.startswith("[Result"):
                print("  [x] Game ended {}".format(i[1:-1]))
        open("./results/{}.pgn".format(body["identifier"]), "a+").write(body["result"])
        ch.basic_ack(delivery_tag = method.delivery_tag)
        print(' [*] Waiting for results. To exit press CTRL+C')

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='lc0-submit', on_message_callback=callback)

    print(' [*] Waiting for results. To exit press CTRL+C')
    channel.start_consuming()

main()