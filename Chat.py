import serial as serial
import time as time
import re as re
import threading


def set_port(s,address):

    #s = serial.Serial(port, 115200,timeout=1)

    ad = "a[" + address + "]\n"

    s.write(ad.encode()) #set the device address to AB

    time.sleep(0.2) #wait for settings to be applied
    
    s.write(b"c[1,0,5]\n") #set number of retransmissions to 5

    time.sleep(0.2) #wait for settings to be applied

    s1.write(b"c[0,1,30]\n") #set FEC threshold to 20 (apply FEC to packets with payload >= 20)

    time.sleep(0.2) #wait for settings to be applied

    #print (ad)
    
def send_msg (s,dest,msg):

    m = "m["+ msg + "\0," + dest + "]\n"

    s.write(m.encode())
    #print (m)


#read from the device’s serial port (should be done in a separate thread) 
def read_msg (s):
    message = "" 
    bool = True
    #i = 1
    stop_thread = False;

    while bool: #while not terminated 
        #print (i)
        #i +=1
        stop_thread= False
        try: 

            byte = s.read(1) #read one byte (blocks until data available or timeout reached) 
            #print (byte)

            if byte ==b'\n': #if termination character reached
                
                #print (message)
                x = re.findall("R,D", message)
                if x and message[0]=="m":

                    print (message) #print message
                    stop_thread=True
                    if stop_thread:
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


#main
print ("Start Chat")

s1 = serial.Serial('/dev/tty.usbmodem14101', 115200,timeout=1)
s2 = serial.Serial('/dev/tty.usbmodem14201', 115200,timeout=1)

set_port (s1,"AB")

set_port (s2, "CD")

Chat = True 

while Chat :

    sender = input ("Choose Sender A or B or close:")

    if sender == "A" or sender == "a":

        msg = input ("Enter message:")

        t1 = threading.Thread (target = send_msg, args = [s1, "FF", msg])

        t1.start()

        t2 = threading.Thread (target = read_msg, args = [s2])

        t2.start()

    

        t1 = threading.Thread (target = read_msg, args = [s1])
        
        time.sleep(0.5)

        t1.start()

        time.sleep (0.5)

        stop_thread=True


        
    elif sender == "B" or sender == "b":

        msg = input ("Enter message:")

        t2 = threading.Thread (target = send_msg, args = [s2, "FF", msg])

        t2.start()

        t1 = threading.Thread (target = read_msg, args = [s1])

        t1.start()
        
        t2 = threading.Thread (target = read_msg, args = [s2])

        time.sleep(0.5)
        
        t2.start()

        time.sleep (0.5)

        stop_thread=True

    elif sender == "Close" or sender == "close":

        Chat = False
        print ("Close Chat")
    else:
        print ("invalid input")



    time.sleep(0.2)





