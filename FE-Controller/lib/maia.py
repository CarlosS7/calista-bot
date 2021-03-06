# coding=utf-8
from __future__ import print_function
import sys

import websocket
import time
import json

from unidecode import unidecode

import threading, Queue

class Maia:

    def __init__ (self, uri, logger):
        """
        Creates the maia object, but does NOT create the websocket
        """

        self.uri = uri
        self.logger = logger

        # Creates the queues for the messages
        self.rcvd_msgs = {}
        self.rcvd_msgs['anonymous'] = Queue.Queue()
        self.lock = threading.Lock()


    def connect(self):
        """
        Connects to the maia network
        """
        self.logger.info("Subscribing to the maia network...")

        # I don't really like this, I should probably
        # just make them private methods or something...
            

        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(self.uri, on_message = self.on_message,
                                                   on_error = self.on_error,
                                                   on_close = self.on_close,
                                                   on_open = self.on_open)
        self.ws.send_type = 'message'
        #self.ws.on_open = Maia.on_open
        self.ws.subscribe = 'message' #lista a suscribirse
        self.ws.response = ''

        self.maia_thread = maiaListener(self.ws)

        self.maia_thread.start()
            
        #ws.run_forever()

    def wait_for_message(self, timeout, user):
        """
        Waits for a message from the maia network, 
        or until the timeout triggers
        """
        
        # Dirty, pass the current query user so I could use the message

        # I get a message from the queue, with timeout.
        # If the timeout triggers, I return an empty string
        response = u""
        try:
            if user in self.rcvd_msgs:

                # I wait until no more messages are received
                while (True):
                    msg = unicode(self.rcvd_msgs[user].get(True, timeout))
                    self.logger.info(u"Received from maia>> " + msg)
                    
                    # I may receive duplicated messages
                    if msg not in response:
                        response +=msg
        except Queue.Empty:
            # Log error?
            self.logger.debug(u"[user: {user}] Maia timeout. continuing...".format(user=user))
            
        return response

    def send(self, data, user):
        """
        Sends a message to the maia network, without waiting for response
        """

        with self.lock:
            self.rcvd_msgs[user] = Queue.Queue()
        self.logger.info('[user: '+user+'] Sending to Maia {"name":"message","data": {"name" : "'+data+'"}}')
        self.ws.send('{"name":"message","data": {"name" : "%s"}}' % data)
        # Bassically, I just add it to the queue.
        #self.send_msgs.put(message)

    def on_open(self, ws):
        """
        When creating the socket, subscribe to the maia network
        """

        ws.send('{"name":"username","data": {"name" : "%s"}}' % "python_client");
        time.sleep(1);
    
        ws.send('{"name":"subscribe","data": {"name" : "%s"}}' % 'message');
        time.sleep(2)
                
    def on_message(self, ws, message):
        """
        Receives a message from the maia network.
        """
        if type(message) == str:
            message = unicode(message, "utf-8")

        # Only attend messages that are actual responses:
        if u"¬maiaResponse" not in message:
            return

        self.logger.debug("Received from maia: " + message)
        userStart = message[message.rfind("[user"):]
            
        user = userStart[:userStart.find("]")+1]
        # Delete the user for the data to send to ChatScript
        mymsg = json.loads(message.replace(user, ""))

        # Replaces the user tags, and keep only the username
        user = user.replace("[user ", "")
        user = user.replace("]", "")

        if u'¬maiaResponse' in mymsg['data']['name']:
            
             msg = mymsg['data']['name']
             
             #Convert the message to utf-8
             if type(msg)==str:
                    msg = unicode(msg, "utf-8")
             
             if user in self.rcvd_msgs:
                self.rcvd_msgs[user].put(msg)
                
    def on_error(self, ws, error):
        """
        Just print the error for the time being
        """
        
        self.logger.error(error)

    def on_close(self, ws):
        """
        Unsubscribe from maia
        """
        self.logger.warning('I still need to figure out how to properly close the maia websocket...')
        
        # Unsubscribe
        # Should I really do this?
        #self.ws.send('{"name":"unsubscribe","data": {"name" : "%s"}}' % 'message')
        #self.ws.close()

        self.maia_thread.join()

class maiaListener(threading.Thread):
    """
    Thread to listen /send messages to the maia network
    """

    def __init__(self, ws):
        super(maiaListener, self).__init__()
        
        # I want the thread to die when CTRL+C is issued, so I make it a "dameon" thread
        self.daemon = True

        self.ws = ws

    def run(self):
        """
        Keeps running
        If I need to send a message, sent it
        """
        self.ws.run_forever()

    def join(self, timeout=None):
        super(maiaListener, self).join(timeout)

