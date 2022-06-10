from socket import *
import os
import sys
import struct
import time
import select
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
        if whatReady[0] == []:  # Tempo limite
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # Fill in start
        # Busca o cabeçalho ICMP do pacote IP

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
    #  O cabeçalho é tipo (8),código (8), soma de verificação (16), id (16), sequência (16)
    myChecksum = 0
    # cabeçalho fictício com uma soma de verificação 0
    # struct -- Interpreta strings como dados binários compactados
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calcula a soma de verificação nos dados e no cabeçalho fictício.
    myChecksum = checksum(header + data)

    # Obtem a soma de verificação correta e coloque no cabeçalho

    if sys.platform == 'darwin':
        # Converte inteiros de 16 bits do host para a ordem de bytes da rede
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1))  #  O endereço AF_INET deve ser tupla, não str

    # Tanto LISTS quanto TUPLES consistem em vários objetos
    # que pode ser referenciado por seu número de posição dentro do objeto


def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")

    # SOCK_RAW é um tipo de soquete poderoso. For more details:   https://sock-raw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF  #  Retorna o processo atual i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay


def ping(host, timeout=1):

    # timeout=1 significa: Se passar um segundo sem resposta do servidor
    #  o cliente assume que o ping do cliente ou o ping do servidor foi perdido
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    # Envia solicitações de ping para um servidor separadas por aproximadamente um segundo
    Rtts = list()
    cont = 0
    cont_losses = 0
    cont_sent = 0
    porc = 0
    while cont <= 3:
        delay = doOnePing(dest, timeout)
        Rtts.append(delay)
        print(f'Resposta de {dest}: bits=16 tempo:{round(delay*1000, 2)}ms')
        time.sleep(1) # um segundo
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




