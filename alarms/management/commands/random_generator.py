import time
import random
import json
from channels import Group
from django.core.management import BaseCommand


class Command(BaseCommand):

    msg = "Sending msg..."

    print(10*"-")
    print("Test01 - Test script to send messages")
    print(10*"=")
    print("Sending random messages for 10 seconds ...")

    def handle(self, *args, **options):

        tstart = time.time()

        i = 1
        while (time.time() - tstart <= 10):

            print ("Sending message {}...".format(i))

            Group("alarms_group").send(
                {"text": json.dumps({"h": random.random()})}
            )
            time.sleep(2)  # send a message each 2 seconds

            i += 1

        print("Messages were sent. Closing.")
        print(10*"-")
