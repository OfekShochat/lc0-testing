import pika
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', credentials=pika.credentials.PlainCredentials("ghostway", "1b283bd00c334a44b096bd66cd61ed5b")))
channel = connection.channel()
channel.queue_delete(queue='lc0-jobs')
