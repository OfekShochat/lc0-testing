from b_rabbit import BRabbit
import sys
import os
import json
from time import sleep
from xxhash import xxh32
from random import random
from subprocess import STDOUT, check_call, CalledProcessError

FNULL = open(os.devnull, 'w')

def build(engine):
    os.system("set CC=cl && set CXX=cl && set CC_LD=link && set CXX_LD=link")

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

    if build_opt["cudnn"] == "true": os.system("set PATH=%CUDA_PATH%\\bin;%PATH%")
    blas = "true"
    if build_opt["mkl"] == "false" and build_opt["dnnl"] == "false" and build_opt["openblas"] == "false" and build_opt["eigen"] == "false": blas = "false"

    os.chdir("./{}/lc0-master".format(engine["identifier"]))
    try:
        check_call("""meson build --backend {} --buildtype release -Ddx={} -Dcudnn={} -Dplain_cuda={} 
    -Dopencl={} -Dblas={} -Dmkl={} -Dopenblas={} -Ddnnl={} -Dgtest={} 
    -Dcudnn_include="{}" -Dcudnn_libdirs="{}" 
    -Dmkl_include="{}\\include" -Dmkl_libdirs="{}\\lib\\intel64" -Ddnnl_dir="{}"
    -Dopencl_libdirs="{}" -Dopencl_include="{}" 
    -Dopenblas_include="{}\\include" -Dopenblas_libdirs="{}\\lib" 
    -Ddefault_library=static""".format(backend, build_opt["dx12"], build_opt["cudnn"], build_opt["cuda"], 
        build_opt["opencl"], blas, build_opt["mkl"], build_opt["openblas"], 
        build_opt["dnnl"], "false", cudnn_include, cudnn_lib_path, build_opt["mkl_path"], 
        build_opt["mkl_path"], build_opt["dnnl_path"], build_opt["opencl_lib_path"], 
        build_opt["cuda_path"], build_opt["openblas_path"], build_opt["openblas_path"]), stdout=FNULL, stderr=FNULL, shell=True)

        os.chdir("./build")
        check_call("msbuild /m /p:Configuration=Release /p:Platform=x64 /p:WholeProgramOptimization=true /p:PreferredToolArchitecture=x64 lc0.sln /filelogger", stderr=STDOUT)

    except CalledProcessError:
        print("building {} is not succesful. exiting...".format(engine["name"]))
        exit(1)

    os.chdir(cur_dir)

def makecmd(engine):
    p = os.path.join(str(engine["identifier"]), "lc0-master", "build", "lc0.exe")
    return p + " -w ./703810.pb.gz"

def cutechess_string(j):
    cutechess_path = "./cutechess"
    if os.name == "nt":
        cutechess_path = os.path.join(cutechess_path, "cutechess-windows.exe")
    else:
        cutechess_path = os.path.join(cutechess_path, "cutechess-linux")
    return """{} -engine name={} cmd={} -engine name={} cmd={} -rounds 1 -pgnout out.pgn -bookmode disk -openings file="book.pgn" order=random plies=100 format=pgn -each proto=uci tc={}""".format(
        cutechess_path,
        j["engine1"]["name"], 
        makecmd(j["engine1"]), 
        j["engine2"]["name"], 
        makecmd(j["engine2"]),
        j["tc"]
    )

def download(link, out, unzip=True, verbose=False):
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

def executejob(j):
    print(" [x] downloading")
    print("  - " + j["engine1"]["name"] + "...")
    download(j["engine1"]["link"], j["engine1"]["identifier"])
    print("  - " + j["engine2"]["name"] + "...")
    download(j["engine2"]["link"], j["engine2"]["identifier"])

    print(" [x] building")
    print("  - " + j["engine1"]["name"] + "...")
    build(j["engine1"])
    print("  - " + j["engine2"]["name"] + "...")
    build(j["engine2"])

    print(" [x] generating cutechess string")
    cutechess_string(j)

def authenticate(j, ch, method, properties):
    return True

# cutechess-cli.exe -engine name=lc0-regular cmd="C:\Users\User\Downloads\lc02\lc0-master\build\lc0.exe -w C:\Users\User\Downloads\lc0-master\lc0-master\703810.pb.gz 
# --threads=1 --smart-pruning-factor=0.0 --minibatch-size=1 --max-prefetch=0" -engine name=lc0-confidence-naive cmd="C:\Users\User\Downloads\lc0-master\lc0-master\build\lc0.exe -w C:\Users\User\Downloads\lc0-master\lc0-master\703810.pb.gz --threads=1 --smart-pruning-factor=0.0 --minibatch-size=1 --max-prefetch=0" -each proto=uci tc=inf nodes=1000 
# -rounds 1 -pgnout C:\Users\User\Downloads\out10.pgn -bookmode disk -openings file="C:\Users\User\Downloads\book_3moves_cp25-49_13580pos (1).pgn" order=random plies=100 format=pgn -concurrency 2

def getcutechess():
    print("getting cutechess")
    if not os.path.isdir("cutechess"): os.mkdir("cutechess")
    download("https://github.com/AndyGrant/OpenBench/blob/master/CoreFiles/cutechess-linux?raw=true", "./cutechess/cutechess-linux", False)
    download("https://github.com/AndyGrant/OpenBench/blob/master/CoreFiles/cutechess-windows.exe?raw=true", "./cutechess/cutechess-windows.exe", False)
def main():

    if not os.path.isdir("cutechess") or not os.path.exists("./cutechess/cutechess-linux") or not os.path.exists("./cutechess/cutechess-windows.exe"):
        getcutechess()

    rabbit = BRabbit(host='localhost', port=5672)

    def callback(server, body):
        print(" [x] Received job")
        j = json.loads(body.decode())
        executejob(j["job"])
        server.send_return(payload=open("file.pgn").read())
        open("file.pgn", "w")
        print(" [*] Finished")
        print(' [*] Waiting for jobs. To exit press CTRL+C')


    taskExecuter = rabbit.TaskExecutor(b_rabbit=rabbit,
                                    executor_name='lc0-testing-queue',
                                    routing_key='lc0-testing-queue.createNewGeofence',
                                    task_listener=callback)

    print(' [*] Waiting for jobs. To exit press CTRL+C')
    taskExecuter.run_task_on_thread()   

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)