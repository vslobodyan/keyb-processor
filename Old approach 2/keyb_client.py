import socket
import sys
 
def Main():
	host = '127.0.0.1'
	port = 5001
	 
	mySocket = socket.socket()
	mySocket.connect((host,port))

	message = ' '.join(sys.argv[1:])

	if message:
		mySocket.send(message.encode())
		data = mySocket.recv(1024).decode()
		 
		print ('Received from server: ' + data)			
	 
	# message = input(" -> ")
	 
	#while message != 'q':
	#        mySocket.send(message.encode())
	#        data = mySocket.recv(1024).decode()
	#         
	#        print ('Received from server: ' + data)
	#         
	#        message = input(" -> ")
			 
	mySocket.close()
 
if __name__ == '__main__':
    Main()
