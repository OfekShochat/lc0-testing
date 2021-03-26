import pika
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_delete(queue='hello')
channel.queue_delete(queue='job-queue')
channel.queue_delete(queue='job-queue1')
channel.queue_delete(queue='lc0-poopoo-queue')
