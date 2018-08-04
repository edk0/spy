import array
import codecs
import os
import json
import os.path
from socket import socket, socketpair, CMSG_SPACE, SOL_SOCKET, SCM_RIGHTS, AF_UNIX, SOCK_STREAM, SHUT_RDWR, SHUT_WR
import socket
import sys

cli_main = None
is_server = False


def serve(sock):
    global cli_main
    from .cli import main
    cli_main = main
    while True:
        conn, addr = sock.accept()
        pid = os.fork()
        if pid == 0:
            try:
                sock.close()
                try:
                    client(conn, addr)
                finally:
                    sys.exit()
            finally:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
        else:
            conn.close()


def client(conn, addr):
    global is_server
    is_server = True
    fds = array.array('i')
    data, ancdata, _, _ = conn.recvmsg(1, socket.CMSG_SPACE(4 * fds.itemsize))
    if len(ancdata) != 1:
        return
    level, type_, data = ancdata[0]
    if level != socket.SOL_SOCKET or type_ != socket.SCM_RIGHTS:
        return
    fds.frombytes(data[:len(data) // fds.itemsize * fds.itemsize])
    fds = fds.tolist()
    if len(fds) != 4:
        return
    try:
        testfd = os.dup(fds[0])
        os.close(testfd)
    except OSError:
        return
    os.dup2(fds[0], 0)
    os.dup2(fds[1], 1)
    os.dup2(fds[2], 2)
    cr = open(fds[3], mode='r')
    cw = open(fds[3], mode='w')
    cmd = json.load(cr)
    sys.argv = cmd
    try:
        cli_main()
    except SystemExit as e:
        code = e.code or 0
        cw.write('%d\n' % code)
    finally:
        try:
            cw.close()
        except OSError:
            pass


def create_server():
    path = os.path.expanduser('~/.spy.sock')
    try:
        os.remove(path)
    except OSError:
        pass
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(path)
    sock.listen()
    pid = os.fork()
    if pid > 0:
        sock.close()
        return
    try:
        serve(sock)
    except Exception as e:
        sys.exit()


def run_on_server():
    path = os.path.expanduser('~/.spy.sock')
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(path)
    control, rc = socket.socketpair()
    fds = array.array('i')
    fds.fromlist([0, 1, 2, rc.fileno()])
    sock.sendmsg([b'x'], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, fds.tobytes())])
    rc.close()
    cr = control.makefile('r')
    cw = control.makefile('w')
    json.dump(sys.argv, cw)
    cw.flush()
    control.shutdown(socket.SHUT_WR)
    l = cr.readline()
    if l:
        sys.exit(int(l.strip()))
    else:
        sys.exit(-1)
