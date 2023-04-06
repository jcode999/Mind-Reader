import subprocess, sys
import os
#Install necessary modules for speech recognition usage.
#subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'SpeechRecognition', 'keyboard', 'PocketSphinx', 'pyaudio'])
import speech_recognition as sr
import socket
import hashlib
import base64
import keyboard
from nlp import preProcess,identify_command



def voice_to_text():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print('Please give your command. Listening...')

        audio = r.listen(source)

        try:
            cmd =  r.recognize_google(audio)
            print('Did you say : ' + cmd)
            return str(cmd)


        except Exception as e:
            print("Error r "+ str(e) )
    

def handle_syn_ack(clientsocket):
    #syn msg is received from the client upon successful connection
    syn_request = clientsocket.recv(2000)
    print('syn_request ',syn_request)
    request = syn_request.decode('utf-8')
    #collect key to generate accept key
    keys_pos = request.find('Sec-WebSocket-Key')
    start_pos = keys_pos + 19 #watch out! This may change in future.
    end = start_pos + 24
    key = request[start_pos:end]
    h = hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode('utf-8'))
    accept = bytes(base64.b64encode(h.digest()))

    #send ack message to client
    clientsocket.sendall(b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+accept+b'\r\n\r\n')
    print('Handshake Complete with client ',clientsocket.getsockname())
    

#Port to connect to VSCode using.
def tcp_connection():
    TCP_PORT = 12152
    print('Starting server .. [pid] : ',os.getpid())
    #Start server socket to communicate.
    serversocket = socket.socket()
   
    serversocket.bind(('', TCP_PORT))
    serversocket.listen()
    print('Server Socket Created and Listening: \n Server:',serversocket)
    clientsocket, clientaddr = serversocket.accept()
    print('[connected with client]: ',clientsocket)
    print('[clienaddr]: ',clientaddr)
    handle_syn_ack(clientsocket) #initail handshake
    #Connect to VSCode client code.
    user_input = ''
    while user_input!='Exit': # TO-DO: compare with messag from voice-to-text later.
        #send message to client
        user_input = voice_to_text()
        entities,action = preProcess('can you '+ user_input,True)
        command_to_run = identify_command(entities,action)
        msg = bytes(command_to_run.encode('utf-8'))
        print('sending message to client: ',msg)
        msg_len = int(hex(len(msg)),16)
    
        #a message should be sent following the websocket protocol.

        # Create a websocket frame containing the message
        frame = bytearray()
        
        # Append frame header, (use hexadecimal) 
        frame.append(0x81)  # FIN + OpCode (1 byte)
        frame.append(msg_len)  # Payload length (msg_len byte), 
        # Append payload
        frame.extend(msg)
        
        #send message to client
        clientsocket.send(frame)
        #break
    #clientsocket.close()

if __name__ == '__main__':
   tcp_connection()