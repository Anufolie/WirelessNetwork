import serial as serial
import time as time
import re as re
import threading

import sys
import serial.threaded as th

global k
global l
global stop_thread
stop_thread = False
k= 0
l=0

def set_port(s,address):

    #s = serial.Serial(port, 115200,timeout=1)

    ad = "a[" + address + "]\n"

    s.write(ad.encode()) #set the device address to AB

    time.sleep(1) #wait for settings to be applied
    
    s.write(b"c[1,0,5]\n") #set number of retransmissions to 5

    time.sleep(0.5) #wait for settings to be applied

    s1.write(b"c[0,1,30]\n") #set FEC threshold to 20 (apply FEC to packets with payload >= 20)

    time.sleep(0.5) #wait for settings to be applied

    #print (ad)
    
def send_msg (s,dest, i):

    msg ="AbcdefghijklmnopqrstuvwxyZAbcdefghijklmnopqrstuvwx" + str(i)
    
    m = "m["+ msg + "\0," + dest + "]\n"
    s.write(m.encode())
    print ("message sent")

    #print (m)

def send_ACK (s,dest,i):

    msg ="ACK" + str(i)

    m = "m["+ msg + "\0," + dest + "]\n"

    s.write(m.encode())
    print ("ack sent")

def read_msg (s):
    message = "" 
    bool = True
    global stop_thread
    #i = 1
    stop_thread = False;

    #global l

    while bool: #while not terminated 
        #print (i)
        #i +=1
        #stop_thread= False
        try: 

            byte = s.read(1) #read one byte (blocks until data available or timeout reached) 
            #print (byte)

            if byte ==b'\n': #if termination character reached
                
                #print (message)
                x = re.findall("R,D", message)
                if x and message[0]=="m":
                    print(message)
                    l = int(re.search(r'\d+', message).group())
                    stop_thread=True
                    break

                #bool = False

                message = "" #reset message

            else:
                
                message = message + byte.decode("utf-8") #concatenate the message 
                #print(message)

            if stop_thread:
                break
        
        
        except serial.SerialException: 

            continue #on timeout try to read again 

        except KeyboardInterrupt: 

            sys.exit() #on ctrl-c terminate program 

def read_ACK (s):
    message = "" 
    bool = True
    #i = 1
    global k
    global stop_thread

    while bool: #while not terminated 
        #print (i)
        #i +=1
        try: 

            byte = s.read(1) #read one byte (blocks until data available or timeout reached) 
            #print (byte)

            if byte ==b'\n': #if termination character reached
                
                #print (message)
                x = re.findall("R,D", message)
                if x and message[0]=="m": #check if message 
                    print (message) #print message
                    k = int(re.search(r'\d+', message).group())
                    k+=1
                    stop_thread=True
                    break
                    
                #bool = False

                message = "" #reset message

            else:
                
                message = message + byte.decode("utf-8") #concatenate the message 
                #print(message)
        except serial.SerialException: 

            continue #on timeout try to read again 

        except KeyboardInterrupt: 

            sys.exit() #on ctrl-c terminate program 

def read_board (s):
    global stop_thread
    message = "" 
    bool = True
    #i = 1
    stop_thread = False;

    while bool: #while not terminated 
        #print (i)
        #i +=1
        #stop_thread= False
        try: 

            byte = s.read(1) #read one byte (blocks until data available or timeout reached) 
            #print (byte)

            if byte ==b'\n': #if termination character reached
                
                #print (message)
                
                if message =="m[D]":
                    print (message)
                    stop_thread=True
                    break

                #bool = False

                message = "" #reset message

            else:
                
                message = message + byte.decode("utf-8") #concatenate the message 
                #print(message)

            if stop_thread:
                break
        
        
        except serial.SerialException: 

            continue #on timeout try to read again 

        except KeyboardInterrupt: 

            sys.exit() #on ctrl-c terminate program 


def send_saturation(s):
    j = 0
    m = 0
    global k

    timeout = time.time() + 60*2
    start = time.time()
    while True:
        
        #for x in range (0,5):
        if j !=k:
            send_msg(s, "CD",k)
            time.sleep (0.01)
            j = k
            print(str(k) +"/" + str(m))
            
        else :
                
            send_msg(s, "CD",j)
            time.sleep(0.01)
            print(str(j) +"/" + str(m))
        j+=1
        m+=1
       
        
        read_board(s)

        #for x in range (0,5):    
        read_ACK(s)
        end = time.time()
        if time.time() > timeout:
            break
        print (end-start)

def read_continuous(s):

    global l
    timeout = time.time() + 60*2
    while True:
        #for x in range (0,5):
        read_msg(s)
        send_ACK(s,"C3",l)
        read_board(s)

       

        if time.time() > timeout:
            break


#main
print ("Start MAC")

s1 = serial.Serial('/dev/tty.usbmodem14101', 115200,timeout=1)
s2 = serial.Serial('/dev/tty.usbmodem14201', 115200,timeout=1)

set_port (s1,"C3")

set_port (s2, "CD")


t1 = threading.Thread (target = send_saturation, args = [s1])
t2 = threading.Thread (target = read_continuous, args = [s2])

t1.start()
t2.start()
