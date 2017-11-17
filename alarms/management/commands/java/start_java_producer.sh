# !/bin/bash

echo 'Run this script from: /ias-webserver/alarms/management/commands/java/'

# compile java classes using py4j
javac -cp ../../../../venv/share/py4j/py4j0.10.6.jar test/src/test/*.java

# run the java application with the producer
cd ./test/src/
java -cp ../../../../../../venv/share/py4j/py4j0.10.6.jar:. test.JavaProducerApp
