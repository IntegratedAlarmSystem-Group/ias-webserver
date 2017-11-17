import time
import random
import json
from channels import Group
from django.core.management import BaseCommand

from py4j.java_gateway import JavaGateway


class Command(BaseCommand):
    """ Required py4j

        *  Related java application should be executed before this program

    """

    print(10*"-")
    print("Test03 - Test script to send messages from java object")
    print(10*"=")
    print("Waiting for messages from java object ...")
    print("* Expected use of py4j. Check compilation instructions.")
    print(10*"-")

    def handle(self, *args, **options):

        gateway = JavaGateway()

        app = gateway.entry_point

        tstart = time.time()

        while (time.time() - tstart < 10):

            # data = {"topic": topic, "value": msg.value.decode("utf-8")}
            data = {"source": "java", "value": app.getMessage()}
            print(data, '\n')

            Group("alarms_group").send({"text": json.dumps(data)})
            time.sleep(1)
        print("Messages were sent. Closing.")
        #  app.close()  # TODO: to review the use of this function
