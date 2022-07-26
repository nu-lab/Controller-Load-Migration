import socket
import sys

if __name__ == "__main__":
    msg = sys.argv[1]
    ip = sys.argv[2]
    port = int(sys.argv[3])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(msg, (ip, port))
    sock.close()
    print("sent message: {}".format(msg))
    sys.stdout.flush()
    sys.stderr.flush()
