import pika
import sys
import os
import json
from time import sleep, time, ctime
from random import random
from subprocess import STDOUT, check_call, CalledProcessError, check_output
from shutil import rmtree
import stat

FNULL = open(os.devnull, 'w')
PASSWORD = "poopookaki"
USERNAME = "poop"

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

def makecmd(engine):
    p = os.path.join("engines", str(engine["identifier"]), "build", "lc0.exe")
    return p + " -w {}".format(os.path.join(os.getcwd(), "703810.pb.gz"))

def cutechess_string(j):
    cutechess_path = "cutechess"
    if os.name == "nt":
        cutechess_path = os.path.join(".", cutechess_path, "cutechess-windows.exe")
    else:
        cutechess_path = os.path.join(cutechess_path, "cutechess-linux")
    return """{} -engine name={} cmd=\"{}\" -engine name={} cmd=\"{}\" -rounds 1 -pgnout out.pgn -bookmode disk -openings file="book.pgn" order=random plies=100 format=pgn -each proto=uci tc={}""".format(
        cutechess_path,
        j["engine1"]["name"], 
        makecmd(j["engine1"]), 
        j["engine2"]["name"], 
        makecmd(j["engine2"]),
        j["tc"]
    )

def git(link, out):
    try:
        check_call("git clone {} ./engines/{} --recurse-submodules".format(link, out))
        return True
    except:
        return False

def download(link, out, unzip=True, verbose=True):
    from requests import get

    c = get(link).content
    if verbose:
        print("  - download complete")
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

def executejob(j):

    print(" [x] downloading")
    print("  - " + j["engine1"]["name"] + "...")
    build1 = git(j["engine1"]["link"], j["engine1"]["identifier"])
    print("  - " + j["engine2"]["name"] + "...")
    build2 = git(j["engine2"]["link"], j["engine2"]["identifier"])
    print(" [x] building")  

    if build1: 
        print("  - " + j["engine1"]["name"] + "...")
        build(j["engine1"])
    else:
        print("  - " + j["engine1"]["name"], "already built")
    if build2:
        print("  - " + j["engine2"]["name"] + "...")
        build(j["engine2"])
    else:
        print("  - " + j["engine2"]["name"], "already built")
    print(cutechess_string(j))
    print(" [x] starting match")
    check_output(cutechess_string(j))

def getcutechess():
    if not os.path.isdir("cutechess"): os.mkdir("cutechess")
    download("https://github.com/AndyGrant/OpenBench/blob/master/CoreFiles/cutechess-linux?raw=true", "./cutechess/cutechess-linux", False)
    download("https://github.com/AndyGrant/OpenBench/blob/master/CoreFiles/cutechess-windows.exe?raw=true", "./cutechess/cutechess-windows.exe", False)

def main():
    if not os.path.isdir("cutechess") or not os.path.exists("./cutechess/cutechess-linux") or not os.path.exists("./cutechess/cutechess-windows.exe"):
        print("no cutechess instelation found.")
        print("downloading...")
        getcutechess()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', heartbeat=600, blocked_connection_timeout=500))
    channel = connection.channel()

    channel.queue_declare(queue='lc0-jobs', durable=True)

    def send_results():
        channel.basic_publish(exchange='', routing_key='lc0-submit', body=open("out.pgn").read(), # json.dumps(response)
                             properties=pika.BasicProperties(delivery_mode = 2)
                             ) 

    def callback(ch, method, properties, body):
        print(" [x] Received job")
        st = time()
        j = json.loads(body.decode())
        executejob(j["job"])
        send_results()
        ch.basic_ack(delivery_tag = method.delivery_tag)
        os.remove("out.pgn")
        print(" [*] Finished in {}s".format(time() - st))
        print(' [*] Waiting for jobs. To exit press CTRL+C')
        deleteOldEngines()

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