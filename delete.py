import pika
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', credentials=pika.credentials.PlainCredentials("admin", "adminPassword")))
channel = connection.channel()
channel.queue_delete(queue='lc0-jobs')
