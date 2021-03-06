import pika, sys, os, json
from time import sleep
from xxhash import xxh32
from random import random
passwords = open("words.txt").read().split("\n")

def build(engine):
    pass

def makecmd(engine):
    p = os.path.join(str(engine["identifier"]), "lc0-master", "build", "lc0.exe")
    return p + " -w ./703810.pb.gz"

def cutechess_string(j):
    return """cutechess-cli.exe -engine name={} cmd={} -engine name={} cmd={} -rounds 1 -pgnout out.pgn -bookmode disk -openings file="book.pgn" order=random plies=100 format=pgn -each proto=uci tc={}""".format(
        j["engine1"]["name"], 
        makecmd(j["engine1"]), 
        j["engine2"]["name"], 
        makecmd(j["engine2"]),
        j["tc"]
    )

def download(link, out, unzip=True):
    from requests import get

    c = get(link).content
    if unzip:

        if not os.path.isdir("./temp"): os.mkdir("./temp")

        open("./temp/{}".format(str(out)), "wb+").write(c)
        from zipfile import ZipFile, BadZipFile
        try:
            with ZipFile("./temp/{}".format(str(out))) as zfile:
                zfile.extractall(str(out))
        except BadZipFile:
            print("invalid zip.")
        os.remove("./temp/{}".format(str(out)))
    else:
        open(out, "wb+").write(c)

def executejob(j):
    print(" exc job => download")
    download(j["engine1"]["link"], j["engine1"]["identifier"])
    download(j["engine2"]["link"], j["engine1"]["identifier"])

    print(" exc job => generating cutechess string")
    cutechess_string(j)
    print("Done")
    print("starting job...")

def authenticate(j, ch, method, properties):
    return True

# cutechess-cli.exe -engine name=lc0-regular cmd="C:\Users\User\Downloads\lc02\lc0-master\build\lc0.exe -w C:\Users\User\Downloads\lc0-master\lc0-master\703810.pb.gz 
# --threads=1 --smart-pruning-factor=0.0 --minibatch-size=1 --max-prefetch=0" -engine name=lc0-confidence-naive cmd="C:\Users\User\Downloads\lc0-master\lc0-master\build\lc0.exe -w C:\Users\User\Downloads\lc0-master\lc0-master\703810.pb.gz --threads=1 --smart-pruning-factor=0.0 --minibatch-size=1 --max-prefetch=0" -each proto=uci tc=inf nodes=1000 
# -rounds 1 -pgnout C:\Users\User\Downloads\out10.pgn -bookmode disk -openings file="C:\Users\User\Downloads\book_3moves_cp25-49_13580pos (1).pgn" order=random plies=100 format=pgn -concurrency 2

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='job-queue2', durable=True)

    def callback(ch, method, properties, body):
        print(" [*] Received job")
        j = json.loads(body.decode())
        executejob(j["job"])
        ch.basic_ack(delivery_tag = method.delivery_tag)
        print(" [*] Finished")
        print(' [*] Waiting for jobs. To exit press CTRL+C')

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='job-queue2', on_message_callback=callback)

    print(' [*] Waiting for jobs. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)