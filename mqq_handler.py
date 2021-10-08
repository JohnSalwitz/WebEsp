import logging
import paho.mqtt.client as mqtt
import credentials
import time
from threading import Thread


class MQQHandler:

    def __init__(self):
        self._client = None
        self._callback_handlers = {}
        self._message_q = []

    def init(self, clientName):
        self._client = mqtt.Client(clientName)
        self._client.username_pw_set(credentials.mqttUser, credentials.mqttPassword)
        self._client.connect(credentials.mqttServer, credentials.mqttPort)

        # start update loop.
        Thread(target=self.loop).start()

        while not self._client.is_connected():
            time.sleep(0.1)

    # loop is run on 2nd thread.
    def loop(self):
        while self._client is not None:
            time.sleep(0.50)
            rc = self._client.loop()
            if rc != 0:
                print("Non Zero Return Code from MQQT (shutting down MQQT.  (Code:{})".format(rc))
                self.close()
            # send messages.
            if self.is_connected:
                if len(self._message_q) > 0:
                    topic_msg = self._message_q.pop(0)
                    self._client.publish(topic_msg[0], topic_msg[1])

    # sets a callback handler for this topic.  Will also subscribe to this topic if
    # not already subscribed.  Note:  No functionality for removing handlers... yet.
    def add_callback(self, topic, callback_handler):
        if topic not in self._callback_handlers:
            self._subscribe(topic)
            self._callback_handlers[topic] = []

        if callback_handler not in self._callback_handlers[topic]:
            self._callback_handlers[topic].append(callback_handler)

        self._client.on_message = self._callback_handler

    def publish(self, topic, msg):
        self._message_q.append((topic, msg))

    # handles all callbacks and routes to internal handler based on topic.
    def _callback_handler(self, client, obj, msg):
        if msg.topic in self._callback_handlers:
            for handler in self._callback_handlers[msg.topic]:
                handler(client, obj, msg)

    def _subscribe(self, topic, level = 0):
        self._client.subscribe(topic, level)

    @property
    def is_connected(self):
        return self._client is not None and self._client.is_connected()

    def close(self):
        self._client = None

# singleton
mqq_handler = MQQHandler()

def on_message(client, obj, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

if __name__ == "__main__":
    mqq_handler.init("unit test mqq")
    mqq_handler.add_callback("esp/log", on_message)
    mqq_handler.publish("esp/log", "hello from the unit test in mqq_handler")

    while True:
        time.sleep(0.1)