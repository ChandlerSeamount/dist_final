import sys
from socket import *
from lib import Node
import time

MESSAGE_LIMIT = 4096

myLocation = int(sys.argv[1])
myID = int(sys.argv[2])

sizeOfNetwork = 8
numNodes = 3
name = "isengard.mines.edu"
basisPort = 56955

me = Node(sizeOfNetwork, myLocation, name, basisPort, numNodes, myID)

while True:

    command = input("What to do? ")

    commandArr = command.split(' ')

    if commandArr[0] == 'exit':
        me.exit()
    elif commandArr[0] == 'print':
        me.printNetwork()
    elif commandArr[0] == 'E':
        me.printE()
    elif commandArr[0] == 'update':
        me.updateNetworkImage()
    elif commandArr[0] == 'internal':
        me.internalEvent()
    elif commandArr[0] == 'external':
        me.externalSend(int(commandArr[1]))
    elif commandArr[0] == 'snapshot':
        me.getSnapshot()
    elif commandArr[0] == 'move-up':
        me.moveUp()
    elif commandArr[0] == 'move-down':
        me.moveDown()
    elif commandArr[0] == 'move-left':
        me.moveLeft()
    elif commandArr[0] == 'move-right':
        me.moveRight()
    else:
        print('Command not recognized')

    if not me.isActive():
        print('I have exited the network')
        break