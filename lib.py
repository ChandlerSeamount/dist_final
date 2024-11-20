from socket import *
import multiprocessing
from multiprocessing import Manager
import time

class Node():

    # creates a node an places it within its own network image
    def __init__(self, networkSize, location, name, basis, numNodes, id):
        self.active = True

        self.networkSize = networkSize
        self.myLocation = location
        self.myName = name
        self.basis = basis
        self.myPort = self.basis + self.myLocation
        self.numNodes = numNodes
        self.myID = id

        self.manager = Manager()
        # time vector
        self.T = self.manager.list([0]*self.numNodes)
        # connection matrix
        temp = [ [0]*self.numNodes for i in range(self.numNodes)]
        temp[self.myID][self.myID] = 1
        self.S = self.manager.list(temp)
        # latest consistent cut time
        self.L = self.manager.list([0]*self.numNodes)
        # event list
        self.e = self.manager.list([])

        self.snapshot = self.manager.list([])

        self.row = int(self.myLocation / self.networkSize)
        self.column = self.myLocation % self.networkSize

        # initiate a UDP socket
        self.sendSocket = socket(AF_INET, SOCK_DGRAM)
        self.listenSocket = socket(AF_INET, SOCK_DGRAM)
        self.listenSocket.bind(('', self.myPort))

        self.activeNeighbors = self.manager.list([])
        self.connectedNeighbors = self.manager.list([])

        self.listenP = multiprocessing.Process(target=self.listen, args=(self.activeNeighbors,self.connectedNeighbors, self.T, self.S, self.L, self.e, self.snapshot))
        self.listenP.start()

        self.networkImage = []
        self.neighbors = self.calculateNeighbors()
        
        self.checkForNeighbors()
        time.sleep(2)

        self.updateNetworkImage()

    # prints the network image from the node's perspective
    def printNetwork(self):
        # make sure the network image is up to date
        self.updateNetworkImage()
        # print the network in a readable format
        for row in self.networkImage:
            print(row)

        print('')
        print('T: '+ str(self.T))
        print('L: '+ str(self.L))
        print('')
        for row in self.S:
            print(row)
        print('')

    # Determine which parts of the network are reachable
    def calculateNeighbors(self):
        neighbors = []
        for i in range(5):
            for j in range(5):
                neighbors.append([self.row + i - 2, self.column + j - 2])
        neighbors.remove([self.row, self.column])

        return neighbors

    # send a message to all "nearby" ports
    def broadcast(self, message):
        for neighbor in self.neighbors:
            if neighbor[0] < 0 or neighbor[1] < 0:
                continue
            if neighbor[0] >= self.networkSize or neighbor[1] >= self.networkSize:
                continue

            self.send(message, neighbor[0]*self.networkSize + neighbor[1])

    # send to every location in the network
    # the paper uses 'some other broadcast protocol'
    def globalBroadcast(self, message):
        for i in range(self.networkSize*self.networkSize):
            self.send(message, i)

    # broadcast to neighbors a simple 'are you there' message
    def checkForNeighbors(self):
        self.broadcast('Hello?')    

    # updates local image of network
    def updateNetworkImage(self):

        newImage = [ [' ']*self.networkSize for i in range(self.networkSize)]
        newImage[self.row][self.column] = str(self.myID)

        for neighbor in self.neighbors:
            if neighbor[0] < 0 or neighbor[1] < 0:
                continue
            if neighbor[0] >= self.networkSize or neighbor[1] >= self.networkSize:
                continue
            newImage[neighbor[0]][neighbor[1]] = '-'

        for neighbor in self.activeNeighbors:
            newImage[neighbor[0]][neighbor[1]] = str(neighbor[2])

        self.networkImage = newImage

    # sends things in standardized format
    def send(self, message, destinationLocation):
        port = self.basis + destinationLocation
        self.sendSocket.sendto(message+','+str(self.myLocation)+','+str(self.myID)+','+':'.join(map(str, self.T))+','+self.matrixToStr(self.S)+','+':'.join(map(str, self.L)), (self.myName, port))

    # always listening function
    def listen(self, activeNeighbors, connectedNeighbors, T, S, L, e, snapshot):

        # print("listening on port " +str(self.myPort))
        while True:
            message, senderAddr = self.listenSocket.recvfrom(1024)

            # print("received: " + message)
            
            msgSplit = message.split(',')
            msgType = msgSplit[0]
            senderLocation = int(msgSplit[1])
            senderID = int(msgSplit[2])
            senderT = [int(x) for x in msgSplit[3].split(':')]
            tempSenderS = msgSplit[4].split('|')
            senderS = []
            for row in tempSenderS:
                senderS.append([int(x) for x in row.split(':')])
            senderL = [int(x) for x in msgSplit[5].split(':')]

            # print(msgType, senderID, senderT)

            if msgType == 'Hello?':
                # update activeNeighbors
                # remove old location (if it exists)
                for neighbor in activeNeighbors:
                    if neighbor[2] == senderID:
                        activeNeighbors.remove(neighbor)
                # add new location to activeNeighbors
                activeNeighbors.append([int(senderLocation / self.networkSize), senderLocation % self.networkSize, senderID, senderLocation])

                # 'On' from paper
                # add to connected list if not already there
                if senderID not in self.connectedNeighbors:
                    connectedNeighbors.append(senderID)

                    # update T
                    T[self.myID] += 1
                    senderT[senderID] += 1
                    self.updateT(T, T, senderT)
                    # update S
                    tempS = []
                    for row in S:
                        tempS.append(row)
                    tempS[self.myID][senderID] += 1
                    senderS[senderID][self.myID] += 1
                    self.updateS(S, tempS, senderS)

                    # record event in e
                    tempT = []
                    for x in T:
                        tempT.append(x)
                    e.append([tempT, self.myLocation])
                    # update L if S is consistent
                    if self.isSymmetric(S):
                        for i in range(self.numNodes):
                            L[i] = T[i]

                # respond with hello
                self.send('Hello', senderLocation)
                
            elif msgType == 'Hello':
                # update activeNeighbors
                # remove old location (if it exists)
                for neighbor in activeNeighbors:
                    if neighbor[2] == senderID:
                        activeNeighbors.remove(neighbor)
                # add new location to activeNeighbors
                activeNeighbors.append([int(senderLocation / self.networkSize), senderLocation % self.networkSize, senderID, senderLocation])

                # 'On' from paper
                # add to connected list if not already there
                if senderID not in self.connectedNeighbors:
                    connectedNeighbors.append(senderID)
                    # update T
                    T[self.myID] += 1
                    self.updateT(T, T, senderT)
                    # update S
                    tempS = []
                    for row in S:
                        tempS.append(row)
                    tempS[self.myID][senderID] += 1
                    self.updateS(S, tempS, senderS)

                    # record event in e
                    tempT = []
                    for x in T:
                        tempT.append(x)
                    e.append([tempT, self.myLocation])
                    # update L if S is consistent
                    if self.isSymmetric(S):
                        for i in range(self.numNodes):
                            L[i] = T[i]

            elif msgType == 'Goodbye':
                # update activeNeighbors
                # remove old location (if it exists)
                for neighbor in activeNeighbors:
                    if neighbor[2] == senderID:
                        activeNeighbors.remove(neighbor)
                
                # 'Off' from paper
                # remove from connected list
                connectedNeighbors.remove(senderID)
                # update T
                T[self.myID] += 1
                # update S
                tempS = []
                for row in S:
                    tempS.append(row)
                tempS[self.myID][senderID] += 1
                self.updateS(S, tempS, tempS)

                # record event in e
                tempT = []
                for x in T:
                    tempT.append(x)
                e.append([tempT, self.myLocation])
                # update L if S is consistent
                if self.isSymmetric(S):
                    for i in range(self.numNodes):
                        L[i] = T[i]
            
            elif msgType == 'External':
                # 'Receive from P' from paper
                # update T
                T[self.myID] += 1
                self.updateT(T, T, senderT)
                # update S
                tempS = []
                for row in S:
                    tempS.append(row)
                self.updateS(S, tempS, senderS)

                
                # record event in e
                tempT = []
                for x in T:
                    tempT.append(x)
                e.append([tempT, self.myLocation])
                # update L if S is consistent
                if self.isSymmetric(S):
                    for i in range(self.numNodes):
                        L[i] = T[i]

            elif msgType == 'Snapshot?':
                for event in e:
                    if event[0][self.myID] == senderL[self.myID]:
                        self.send('Snapshot|'+str(event[1]), senderLocation)
                        break
            
            elif msgType[:9] == 'Snapshot|':
                msgArr = msgType.split('|')
                snapshot.append([senderID, msgArr[1]])


    def updateLocation(self, newLocation):
        self.myLocation = newLocation
        self.myPort = self.basis + self.myLocation
        self.row = int(self.myLocation / self.networkSize)
        self.column = self.myLocation % self.networkSize

        # stop listening from old location
        self.listenP.terminate()
        self.listenP.join()

        # start listening at new location
        self.listenSocket = socket(AF_INET, SOCK_DGRAM)
        self.listenSocket.bind(('', self.myPort))
        
        # self.activeNeighbors = self.manager.list([])

        self.listenP = multiprocessing.Process(target=self.listen, args=(self.activeNeighbors,self.connectedNeighbors, self.T, self.S, self.L, self.e, self.snapshot))
        self.listenP.start()

        # look at network again
        self.neighbors = self.calculateNeighbors()

        self.checkForNeighbors()
        time.sleep(2)
        self.updateNetworkImage()

    # 'Internal event' from paper
    # simulate an internal event
    def internalEvent(self):
        # update T
        self.T[self.myID] += 1
        # record event in e
        tempT = []
        for x in self.T:
            tempT.append(x)
        self.e.append([tempT, self.myLocation])
        # update L if S is consistent
        if self.isSymmetric(self.S):
            self.L = self.T

    # 'Send to P' from paper
    # send to a given destination (by id) (external event)
    def externalSend(self, destination):
        if destination not in self.connectedNeighbors:
            print('Not connected to node ' + str(destination))
            return
        
        # update T
        self.T[self.myID] += 1
        # record event in e
        tempT = []
        for x in self.T:
            tempT.append(x)
        self.e.append([tempT, self.myLocation])
        # update L if S is consistent
        if self.isSymmetric(self.S):
            self.L = self.T

        for neighbor in self.activeNeighbors:
            if neighbor[2] == destination:
                self.send('External', neighbor[3]) # neighbor location
                break

    def getSnapshot(self):
        self.snapshot[:] = []
        self.globalBroadcast('Snapshot?')
        time.sleep(2)
        for row in self.snapshot:
            print(row)

    # compare 2 vectors and update the first with the most recent values
    # arr0 = vector to store result
    # arr1 and arr2 = vectors to compare
    def updateT(self, arr0, arr1, arr2):
        for i in range(self.numNodes):
            arr0[i] = max(arr1[i], arr2[i])

    # compare 2 matrices and update the first with the most recent values
    # matrix0 = matrix to store result
    # matrix1 and matrix2 = matrices to compare
    def updateS(self, matrix0, matrix1, matrix2):
        for i in range(self.numNodes):
            for j in range(self.numNodes):
                matrix1[i][j] = max(matrix1[i][j], matrix2[i][j])
            matrix0[i] = matrix1[i]

    # converts a matrix to a string for sending purposes
    def matrixToStr(self, matrix):
        result = ""
        for row in matrix:
            result += ':'.join(map(str, row)) + '|'
        return result[:-1]

    # checks if a 2D array is symmetric
    def isSymmetric(self, matrix):
        for i in range(self.numNodes):
            for j in range(self.numNodes):
                if (matrix[i][j] != matrix[j][i]):
                    return False
        return True

    def isActive(self):
        return self.active

    def printE(self):
        for event in self.e:
            print(event)

    def moveUp(self):
        # self.internalEvent()

        if self.row == 0:
            # Exits network
            self.exit()
        else:
            # let people know you're moving too far away
            for neighbor in self.activeNeighbors:
                if neighbor[0] == self.row+2:
                    self.send('Goodbye', neighbor[3]) # neighbor location
                    # update arrays
                    self.activeNeighbors.remove(neighbor)
                    self.connectedNeighbors.remove(neighbor[2])
                    # update T
                    self.T[self.myID] += 1
                    # update S
                    tempS = []
                    for row in self.S:
                        tempS.append(row)
                    tempS[self.myID][neighbor[2]] += 1
                    self.updateS(self.S, tempS, tempS)
            # move for real
            self.updateLocation(self.myLocation - self.networkSize)
            self.internalEvent()

    def moveDown(self):
        # self.internalEvent()

        if self.row+1 == self.networkSize:
            # Exits network
            self.exit()
        else:
            # let people know you're moving too far away
            for neighbor in self.activeNeighbors:
                if neighbor[0] == self.row-2:
                    self.send('Goodbye', neighbor[3]) # neighbor location
                    # update arrays
                    self.activeNeighbors.remove(neighbor)
                    self.connectedNeighbors.remove(neighbor[2])
                    # update T
                    self.T[self.myID] += 1
                    # update S
                    tempS = []
                    for row in self.S:
                        tempS.append(row)
                    tempS[self.myID][neighbor[2]] += 1
                    self.updateS(self.S, tempS, tempS)

            # move for real
            self.updateLocation(self.myLocation + self.networkSize)
            self.internalEvent()

    def moveLeft(self):
        # self.internalEvent()

        if self.column == 0:
            # Exits network
            self.exit()
        else:
            # let people know you're moving too far away
            for neighbor in self.activeNeighbors:
                if neighbor[1] == self.column+2:
                    self.send('Goodbye', neighbor[3]) # neighbor location
                    # update arrays
                    self.activeNeighbors.remove(neighbor)
                    self.connectedNeighbors.remove(neighbor[2])
                    # update T
                    self.T[self.myID] += 1
                    # update S
                    tempS = []
                    for row in self.S:
                        tempS.append(row)
                    tempS[self.myID][neighbor[2]] += 1
                    self.updateS(self.S, tempS, tempS)
            # move for real
            self.updateLocation(self.myLocation - 1)
            self.internalEvent()

    def moveRight(self):
        # self.internalEvent()

        if self.column+1 == self.networkSize:
            # Exits network
            self.exit()
        else:
            # let people know you're moving too far away
            for neighbor in self.activeNeighbors:
                if neighbor[1] == self.column-2:
                    self.send('Goodbye', neighbor[3]) # neighbor location
                    # update arrays
                    self.activeNeighbors.remove(neighbor)
                    self.connectedNeighbors.remove(neighbor[2])
                    # update T
                    self.T[self.myID] += 1
                    # update S
                    tempS = []
                    for row in self.S:
                        tempS.append(row)
                    tempS[self.myID][neighbor[2]] += 1
                    self.updateS(self.S, tempS, tempS)
            # move for real
            self.updateLocation(self.myLocation + 1)
            self.internalEvent()

    def exit(self):
        self.broadcast('Goodbye')
        self.listenP.terminate()
        self.listenP.join()
        self.active = False