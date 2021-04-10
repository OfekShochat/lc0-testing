import pika
import sys
import os
import json
from requests import get
from time import sleep, time, ctime
from random import random
from subprocess import STDOUT, check_call, CalledProcessError, check_output
from shutil import rmtree
import stat

FNULL = open(os.devnull, 'w')

class status_obj:
    def __init__(self):
        self.last_updated = time()
    
    def should_update(self):
        if time() - self.last_updated >= 60 * 10:
            return True
        return False

def build(engine):
    check_call("set CC=cl && set CXX=cl && set CC_LD=link && set CXX_LD=link", shell=True, stdout=FNULL, stderr=FNULL)

    cur_dir = os.getcwd()
    build_opt = json.loads(open("./options.json", "r").read())

    if os.path.exists(r"C:\Program Files (x86)\Microsoft Visual Studio\2019"):
        backend = "vs2019"
    elif os.path.exists(r"C:\Program Files (x86)\Microsoft Visual Studio\2017"):
        backend = "vs2017"
    else:
        print("no visual studio instelation found. please install visual studio from https://visualstudio.microsoft.com/downloads/")
        exit(1)
    
    cudnn_lib_path = os.path.join(build_opt["cuda_path"], "lib", "x64")
    cudnn_include = os.path.join(build_opt["cuda_path"],"include")

    if build_opt["cudnn"] == "true": check_call("set PATH=%CUDA_PATH%\\bin;%PATH%", shell=True, stdout=FNULL, stderr=FNULL)
    blas = "true"
    if build_opt["mkl"] == "false" and build_opt["dnnl"] == "false" and build_opt["openblas"] == "false" and build_opt["eigen"] == "false": blas = "false"

    os.chdir("./engines/{}".format(engine["identifier"]))
    try:
        d = check_call("""meson build --backend {} --buildtype release -Ddx={} -Dcudnn={} -Dplain_cuda={} -Dopencl={} -Dblas={} -Dmkl={} -Dopenblas={} -Ddnnl={} -Dgtest=false -Dcudnn_include="{}" -Dcudnn_libdirs="{}" -Dmkl_include="{}\\include" -Dmkl_libdirs="{}\\lib\\intel64" -Ddnnl_dir="{}" -Dopencl_libdirs="{}" -Dopencl_include="{}" -Dopenblas_include="{}\\include" -Dopenblas_libdirs="{}\\lib" -Ddefault_library=static""".format(backend, build_opt["dx12"], build_opt["cudnn"], build_opt["cuda"], 
        build_opt["opencl"], blas, build_opt["mkl"], build_opt["openblas"], 
        build_opt["dnnl"], cudnn_include, cudnn_lib_path, build_opt["mkl_path"], 
        build_opt["mkl_path"], build_opt["mkl_path"], build_opt["dnnl_path"], build_opt["opencl_lib_path"], 
        build_opt["cuda_path"], build_opt["openblas_path"], build_opt["openblas_path"]), stdout=FNULL, stderr=FNULL, shell=True)

        os.chdir("./build")
        check_call("msbuild /m /p:Configuration=Release /p:Platform=x64 /p:WholeProgramOptimization=true /p:PreferredToolArchitecture=x64 lc0.sln /filelogger", stderr=FNULL, stdout=FNULL, shell=True)

    except CalledProcessError as e:
        print("error encountered:", e)
        print("building {} is not succesful. exiting...".format(engine["name"]))
        exit(1)

    os.chdir(cur_dir)

def makecmd(engine, network):
    p = os.path.join("engines", str(engine["identifier"]), "build", "lc0.exe")
    return p + " -w {}".format(os.path.join(os.getcwd(), network))


def getnetwork(engine):
    if engine["network"] == "default":
        return "703810.pb.gz"
    return engine["network"][engine["network"].find("sha=")+4:] + ".pb.gz"

def cutechess_string(j, identifier):
    cutechess_path = "cutechess"
    if os.name == "nt":
        cutechess_path = os.path.join(".", cutechess_path, "cutechess-windows.exe")
    else:
        cutechess_path = os.path.join(cutechess_path, "cutechess-linux")
    return """{} -engine name={} cmd=\"{}\" -engine name={} cmd=\"{}\" -rounds 1 -pgnout out.pgn -bookmode disk -openings file="book.pgn" order=random plies=100 format=pgn -each proto=uci tc={}""".format(
        cutechess_path,
        j["engine1"]["name"], 
        makecmd(j["engine1"], getnetwork(j["engine1"])), 
        j["engine2"]["name"], 
        makecmd(j["engine2"], getnetwork(j["engine2"])),
        j["tc"]
    )

def git(link, out):
    try:
        check_call("git clone {} ./engines/{} --recurse-submodules".format(link, out))
        return True
    except:
        return False

def download(link, out, unzip=True, verbose=True, redirects=True):
    from requests import get

    c = get(link, allow_redirects=redirects).content

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
        if verbose: print("  - unziped")
    else:
        open(out, "wb+").write(c)
        if verbose:
            print("  - download complete")   

def deleteOldEngines():
    def removeGit(func, path, execinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    from glob import glob
    for i in glob("./engines/**"):
        modTime = os.path.getmtime(i)
        if time() - modTime > 18000: # 5 hours
            rmtree(i, onerror=removeGit)
            print(" [*] deleted old engine {}".format(i))

def netNotDownloaded(engine):
    if os.path.exists(getnetwork(engine)):
        return False
    return True

def executejob(j):
    job = j["job"]
    print(" [x] downloading")
    print("  - " + job["engine1"]["name"] + "...")
    build1 = git(job["engine1"]["link"], job["engine1"]["identifier"])
    print("  - " + job["engine2"]["name"] + "...")
    build2 = git(job["engine2"]["link"], job["engine2"]["identifier"])
    if netNotDownloaded(job["engine1"]):
        print("  - getting network {}".format(getnetwork(job["engine1"])))
        download(job["engine1"]["network"], getnetwork(job["engine1"]), redirects=True, unzip=False)
    if netNotDownloaded(job["engine2"]):
        print("  - getting network {}".format(getnetwork(job["engine2"])))
        download(job["engine2"]["network"], getnetwork(job["engine1"]), redirects=True, unzip=False)
    print(" [x] building")  

    if build1: 
        print("  - " + job["engine1"]["name"] + "...")
        build(job["engine1"])
    else:
        print("  - " + job["engine1"]["name"], "already built")
    if build2:
        print("  - " + job["engine2"]["name"] + "...")
        build(job["engine2"])
    else:
        print("  - " + job["engine2"]["name"], "already built")
    print(cutechess_string(job, j["test-identifier"]))
    print(" [x] starting match")
    check_output(cutechess_string(job, j["test-identifier"]))

def getcutechess():
    if not os.path.isdir("cutechess"): os.mkdir("cutechess")
    download("https://github.com/AndyGrant/OpenBench/blob/master/CoreFiles/cutechess-linux?raw=true", "./cutechess/cutechess-linux", False)
    download("https://github.com/AndyGrant/OpenBench/blob/master/CoreFiles/cutechess-windows.exe?raw=true", "./cutechess/cutechess-windows.exe", False)

def getbook():
    download("https://raw.githubusercontent.com/killerducky/OpenBench/lc0/Books/8moves_v3.pgn", "./book.pgn", False)

def update():
    c = get("https://api.github.com/repos/OfekShochat/lc0-testing/worker.pyd").content
    open("worker.pyd", "wb+").write(c)

status = status_obj()

def main():
    #update()
    
    if not os.path.isdir("cutechess") or not os.path.exists("./cutechess/cutechess-linux") or not os.path.exists("./cutechess/cutechess-windows.exe"):
        print("no cutechess instelation found.")
        print("downloading...")
        getcutechess()
    if not os.path.exists("book.pgn"): 
        print("book not found.")
        print("downloading...")
        getbook()

    connection = pika.BlockingConnection(pika.ConnectionParameters(virtual_host="/", credentials=pika.credentials.PlainCredentials("worker", "weDoWorkHere"), host='172.28.93.135', heartbeat=600, blocked_connection_timeout=500))
    channel = connection.channel()

    def send_results(identifier):
        connection = pika.BlockingConnection(pika.ConnectionParameters(virtual_host="results", credentials=pika.credentials.PlainCredentials("worker", "weDoWorkHere"), host='172.28.93.135', heartbeat=600, blocked_connection_timeout=500))
        connection.channel().basic_publish(exchange='', routing_key='lc0-submit', body=json.dumps({"result":open("out.pgn").read(), "identifier":identifier}), # json.dumps(response)
                             properties=pika.BasicProperties(delivery_mode = 2)
                             ) 

    def callback(ch, method, properties, body):
        if status.should_update():
            #update()
            status.last_updated = time()


        print(" [x] Received job")
        st = time()
        j = json.loads(body.decode())
        executejob(j)
        send_results(j["test-identifier"])

        ch.basic_ack(delivery_tag = method.delivery_tag)
        os.remove("out.pgn")
        deleteOldEngines()
        
        print(" [*] Finished in {}s".format(time() - st))
        print(' [*] Waiting for jobs. To exit press CTRL+C')

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='lc0-jobs', on_message_callback=callback)

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