from socket import *
import os
import sys
import struct
import time
import select
import statistics
import binascii

# Should use stdev

ICMP_ECHO_REQUEST = 8


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(string):
        csum += (string[len(string) - 1])
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout

    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # Fill in start

        # Fetch the ICMP header from the IP packet

        icmpHeader = recPacket[20:28]
        icmpType, code, mychecksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        if icmpType != 8 and packetID == ID:
            bytesInDouble = struct.calcsize("d")
        timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
        return timeReceived - timeSent

    # Fill in end
    timeLeft = timeLeft - howLongInSelect
    if timeLeft <= 0:
        return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)

    myChecksum = 0
    # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header

    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network  byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1))  # AF_INET address must be tuple, not str

    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.


def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")

    # SOCK_RAW is a powerful socket type. For more details:   https://sock-raw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay


def ping(host, timeout=1):

    # timeout=1 means: If one second goes by without a reply from the server,
    # the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    Rtts = list()
    cont = 0
    cont_losses = 0
    cont_sent = 0
    porc = 0
    while cont <= 3:
        delay = doOnePing(dest, timeout)
        Rtts.append(delay)
        print(f'Resposta de {dest}: bits=16 tempo:{round(delay*1000, 2)}ms')
        time.sleep(1) # one second
        cont += 1
        if delay < 0:
            cont_losses += 1
        else:
            cont_sent += 1
    porc = (cont_losses/cont)*100
    packetmin = min(Rtts)
    packetmax = max(Rtts)
    packetavg = sum(Rtts) / len(Rtts)
    print()
    print(f'Estatisticas do ping para {dest}:')
    print(f'    Pacotes: Enviados = {cont}, Recebidos = {cont_sent},'
              f' Perdidos = {cont_losses} ({porc}% de perdas)')
    print()
    print(f'Aproximar um numero redondo de vezes em milissegundos')
    print(f'    Mínimo: {round(packetmin*1000, 2)} ms, Máximo: {round(packetmax*1000, 2)}'
            f'ms, Média: {round(packetavg*1000, 2)}ms')
    return vars


if __name__ == '__main__':
    ping('127.0.0.1')
    print()
    ping("google.com")




