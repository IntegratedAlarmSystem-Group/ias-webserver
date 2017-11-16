import time
import random
import json
from channels import Group
from django.core.management import BaseCommand

from kafka import KafkaConsumer


class Command(BaseCommand):
    """ Required apache kafka and zookeeperd

        * Check the status of the apache kafka server before run this test

    """

    print(10*"-")
    print("Test02 - Test script to send messages")
    print(10*"=")
    print("Waiting for messages from kafka-consumer ('topic: test')")
    print("* Expected use of a command line producer")
    print(10*"-")

    def handle(self, *args, **options):

        topic = 'test'

        consumer = KafkaConsumer(topic)

        for msg in consumer:

            print(msg, '\n')

            data = {"topic": topic, "value": msg.value.decode("utf-8")}

            Group("alarms_group").send({"text": json.dumps(data)})
