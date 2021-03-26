from pgn_parser import parser, pgn
import pika

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', heartbeat=600, blocked_connection_timeout=500))
    channel = connection.channel()

    channel.queue_declare(queue='lc0-poopoo-submit', durable=True)

    def callback(ch, method, properties, body):
        print("  [x] Received result")
        for i in body.decode().split("\n"):
            if i.startswith("[White"):
                print("  [x] " + i[1:-1])
            elif i.startswith("[Black"):
                print("  [x] " + i[1:-1])
            elif i.startswith("[Result"):
                print("  [x] Game ended {}".format(i[1:-1]))
        open("results.pgn", "a+").write(body.decode() + "\n\n")
        ch.basic_ack(delivery_tag = method.delivery_tag)
        print(' [*] Waiting for results. To exit press CTRL+C')

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='lc0-poopoo-submit', on_message_callback=callback)

    print(' [*] Waiting for results. To exit press CTRL+C')
    channel.start_consuming()

main()