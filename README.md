# quixotic-kafka
Python Stream Processing for Apache Kafka.

# Why do I need this?

Currently, I have a Unity-ROS simulation setup in a docker container. I am wanting to learn how to publish ROS topic data into a structured streaming pipeline by building an architecture that includes a data source (my Unity-ROS simulation) and  to collect data without any loss, analyze them and store results in a database.

I am thinking something along the lines of the following diagram. I shall utilize ROS (Robot Operating System) as a data provider, Kafka as a message queue, Apache Spark as a data processing engine and Apache Cassandra as a database.

```mermaid
flowchart LR
    subgraph Data Source
        ros(Unity-ROS-noetic<br>Simulation)
    end

    subgraph Structured Streaming
        kafka(Kafka) --> spark(Spark) --> cass(Cassandra)
    end

    ros --> kafka
```

Also, it would be fun to setup a structured streaming pipeline without having to deal with unnecessary headers involved with ROS simulation.

# Setup

Firstly, I have my ROS simulation up and running in a docker. I would want to publish the rostopic data into Kafka (producer). Then I would setup a way to fetch the data from Kafka (consumer).

Setup kafka console on the host machine using the [Quix CLI](https://quix.io/docs/quix-cli/cli-quickstart.html)

```sh
curl -fsSL https://github.com/quixio/quix-cli/raw/main/install.sh | bash
```

To verify you have the dependencies installed, run the following command:

```sh
quix status
```
View the output carefully to confirm you have Git and Docker installed:
```
✗ Not logged in
  User:                       ! Not logged in to Quix Cloud
  Current context:            default (https://portal-api.platform.quix.io)
  Default environment:        ! Not set
  SDK Broker configuration:   Local (localhost:19092)
! Local Pipeline Status:      Not Running
✓ Local Broker Status:        Running (localhost:19092)
✓ Local Broker GUI:           Running (http://localhost:8080)
✓ Docker detected
✓ Git detected
  Git Root:                   /home/vishal/mygithub/quixotic-kafka
```

The following command will create the right docker compose file such that you have a broker running on localhost:19092 and you do not have to worry about setting up the environment variables and the configuration.
```sh
quix pipeline up
```



## Connectivity issues

1. Firstly, I need my ROS docker container to be able to communicate with kafka. For this, I need to setup the `HOST_IP` environment variable and start up the docker compose.

```sh
vishal@vishal:~/mygithub/quixotic-kafka$ hostname -I
10.0.0.82 172.19.0.1 172.17.0.1 172.18.0.1 2601:14b:4501:7440::edf4 2601:14b:4501:7440:81b8:80f:ecf5:86a2 2601:14b:4501:7440:a97a:5401:b552:cbec
```

I will setup a bash script to setup the `HOST_IP` environment variable and start up the docker compose.

```sh
#!/bin/bash

# Get the host IP address
export HOST_IP=$(hostname -I | awk '{print $1}')

# Run Docker Compose
docker compose down && docker compose up -d
```

I shall execute the above bash script that uses the docker compose file below to start the kafka and zookeeper containers.

```yml
services:
  zoo1:
    image: confluentinc/cp-zookeeper:7.3.2
    hostname: zoo1
    container_name: zoo1
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_SERVER_ID: 1
      ZOOKEEPER_SERVERS: zoo1:2888:3888
    networks:
      - my_ros_network

  kafka1:
    image: confluentinc/cp-kafka:7.3.2
    hostname: kafka1
    container_name: kafka1
    ports:
      - "9092:9092"
      - "29092:29092"
    environment:
      KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka1:29092,EXTERNAL://${HOST_IP}:9092
      KAFKA_LISTENERS: INTERNAL://0.0.0.0:29092,EXTERNAL://0.0.0.0:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: INTERNAL
      KAFKA_ZOOKEEPER_CONNECT: "zoo1:2181"
      KAFKA_BROKER_ID: 1
    depends_on:
      - zoo1
    networks:
      - my_ros_network

networks:
  my_ros_network:
    external: true
```

My kafka and zookeeper are on `my_ros_network`. However, my ROS docker container is using `host` network.

2. Next, my ROS docker container needs to connect to the kafka and zookeeper containers.


```sh
vishal@vishal:~$ catkin-docker run
55c0ca9f980ef2553d78664ef64659545619c36894a32c3a8b91609c1df4d9bf
vishal@vishal:~$ docker exec -it 55c0ca9f980ef2553d78664ef64659545619c36894a32c3a8b91609c1df4d9bf /bin/bash
root@vishal:/home/vishal# source docker-build/install/setup.bash
root@vishal:/home/vishal/kafka-producer# cat setup.sh
apt update && apt install python3.8-venv  telnet -y
pip3 install -r requirements.txt
root@vishal:/home/vishal/kafka-producer# ./setup.sh
root@vishal:/home/vishal/kafka-producer# telnet 10.0.0.82 9092
Trying 10.0.0.82...
Connected to 10.0.0.82.
Escape character is '^]'.


Connection closed by foreign host.
```

I am able to connect to the kafka container. Now, I need to push data into kafka.

2. I need to make sure that my ROS simulation is publishing the data into the topic. Since I have not started a simulation, I won't be able to get any data out.

```sh
root@vishal:/home/vishal# rostopic list
ERROR: Unable to communicate with master!
root@vishal:/home/vishal/kafka-producer# python3 kafka_producer.py
Hostname: vishal
IP Address: 10.0.0.82
Unable to register with master node [http://localhost:11311]: master may not be running yet. Will keep trying.
```

```python
import rospy
from nav_msgs.msg import Odometry
import json
from datetime import datetime
from kafka import KafkaProducer
import socket
import subprocess

def get_hostname()->str:
    # Get the hostname
    hostname = socket.gethostname()

    # Get the IP address
    try:
        # Run the 'hostname -I' command and capture its output
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, check=True)
        # Split the output and take the first IP address
        ip_address = result.stdout.split()[0]
    except subprocess.CalledProcessError:
        # If 'hostname -I' fails, fall back to socket method
        ip_address = socket.gethostbyname(hostname)

    print(f"Hostname: {hostname}")
    print(f"IP Address: {ip_address}")
    return str(ip_address)

count = 0
producer = KafkaProducer(bootstrap_servers=[f'{get_hostname()}:9092'],
    value_serializer=lambda message: json.dumps(message).encode('utf-8')
)

def callback(msg):
    global count
    messages = {
        "id": count,
        "posex": float("{0:.5f}".format(msg.pose.pose.position.x)),
        "posey": float("{0:.5f}".format(msg.pose.pose.position.y)),
        "posez": float("{0:.5f}".format(msg.pose.pose.position.z)),
        "orientx": float("{0:.5f}".format(msg.pose.pose.orientation.x)),
        "orienty": float("{0:.5f}".format(msg.pose.pose.orientation.y)),
        "orientz": float("{0:.5f}".format(msg.pose.pose.orientation.z)),
        "orientw": float("{0:.5f}".format(msg.pose.pose.orientation.w))
    }
    print(f"Producing message {datetime.now()} | Message:\n{str(messages)}")
    producer.send("my-topic", messages)
    count += 1  # Increment the count for the next message

if __name__ == "__main__":
    try:
        rospy.init_node('odomSubscriber', anonymous=True)
        rospy.Subscriber('warty/odom', Odometry, callback)
        rospy.spin()
    except rospy.ROSInterruptException:
        print("ROS Node Interrupted")
    finally:
        producer.close()  # Close the Kafka producer connection when the script ends

```


3. Starting a ROS simulation to check if I can push data into kafka.

```sh
root@vishal:/home/vishal/kafka-producer# rostopic list | wc -l
337
root@vishal:/home/vishal/kafka-producer# python3 kafka_producer.py
Hostname: vishal
IP Address: 10.0.0.82
Producing message 2024-10-16 11:56:56.568391 | Message:
{'id': 0, 'posex': 0.0, 'posey': 0.0, 'posez': 0.0, 'orientx': 0.03372, 'orienty': 0.06719, 'orientz': -0.08519, 'orientw': 0.99352}
Producing message 2024-10-16 11:56:56.868415 | Message:
{'id': 1, 'posex': 0.0, 'posey': 0.0, 'posez': 0.0, 'orientx': 0.03369, 'orienty': 0.06719, 'orientz': -0.08519, 'orientw': 0.99353}
Producing message 2024-10-16 11:56:56.868699 | Message:
{'id': 2, 'posex': 0.0, 'posey': 0.0, 'posez': 0.0, 'orientx': 0.03359, 'orienty': 0.0672, 'orientz': -0.08518, 'orientw': 0.99353}
Producing message 2024-10-16 11:56:56.868822 | Message:
{'id': 3, 'posex': 0.0, 'posey': 0.0, 'posez': 0.0, 'orientx': 0.03359, 'orienty': 0.0672, 'orientz': -0.08518, 'orientw': 0.99353}
Producing message 2024-10-16 11:56:56.869439 | Message:
{'id': 4, 'posex': 0.0, 'posey': 0.0, 'posez': 0.0, 'orientx': 0.03363, 'orienty': 0.06719, 'orientz': -0.08518, 'orientw': 0.99353}
Producing message 2024-10-16 11:56:56.869652 | Message:
{'id': 5, 'posex': 0.0, 'posey': 0.0, 'posez': 0.0, 'orientx': 0.03368, 'orienty': 0.06718, 'orientz': -0.08519, 'orientw': 0.99353}
Producing message 2024-10-16 11:56:56.869785 | Message:
{'id': 6, 'posex': 0.0, 'posey': 0.0, 'posez': 0.0, 'orientx': 0.03366, 'orienty': 0.06718, 'orientz': -0.08519, 'orientw': 0.99353}
Producing message 2024-10-16 11:56:56.870448 | Message:
{'id': 7, 'posex': 0.0, 'posey': 0.0, 'posez': 0.0, 'orientx': 0.03374, 'orienty': 0.06718, 'orientz': -0.08519, 'orientw': 0.99352}
Producing message 2024-10-16 11:56:56.870580 | Message:
{'id': 8, 'posex': 0.0, 'posey': 0.0, 'posez': 0.0, 'orientx': 0.03362, 'orienty': 0.06718, 'orientz': -0.08518, 'orientw': 0.99353}
Producing message 2024-10-16 11:56:56.870731 | Message:
{'id': 9, 'posex': 0.0, 'posey': 0.0, 'posez': 0.0, 'orientx': 0.03364, 'orienty': 0.06718, 'orientz': -0.08519, 'orientw': 0.99353}
Producing message 2024-10-16 11:56:56.870786 | Message:
{'id': 10, 'posex': 0.0, 'posey': 0.0, 'posez': 0.0, 'orientx': 0.03368, 'orienty': 0.06718, 'orientz': -0.08519, 'orientw': 0.99353}
```

Alright, seems like we are getting the data to push into kafka. However, I need to check if kafka received the data.

```sh
root@vishal:/home/vishal/kafka-producer# kafkacat -C -b 10.0.0.82:9092 -t my-topic
{"id": 0, "posex": 0.0, "posey": 0.0, "posez": 0.0, "orientx": 0.03372, "orienty": 0.06719, "orientz": -0.08519, "orientw": 0.99352}
{"id": 1, "posex": 0.0, "posey": 0.0, "posez": 0.0, "orientx": 0.03369, "orienty": 0.06719, "orientz": -0.08519, "orientw": 0.99353}
{"id": 2, "posex": 0.0, "posey": 0.0, "posez": 0.0, "orientx": 0.03359, "orienty": 0.0672, "orientz": -0.08518, "orientw": 0.99353}
{"id": 3, "posex": 0.0, "posey": 0.0, "posez": 0.0, "orientx": 0.03359, "orienty": 0.0672, "orientz": -0.08518, "orientw": 0.99353}
{"id": 4, "posex": 0.0, "posey": 0.0, "posez": 0.0, "orientx": 0.03363, "orienty": 0.06719, "orientz": -0.08518, "orientw": 0.99353}
{"id": 5, "posex": 0.0, "posey": 0.0, "posez": 0.0, "orientx": 0.03368, "orienty": 0.06718, "orientz": -0.08519, "orientw": 0.99353}
{"id": 6, "posex": 0.0, "posey": 0.0, "posez": 0.0, "orientx": 0.03366, "orienty": 0.06718, "orientz": -0.08519, "orientw": 0.99353}
{"id": 7, "posex": 0.0, "posey": 0.0, "posez": 0.0, "orientx": 0.03374, "orienty": 0.06718, "orientz": -0.08519, "orientw": 0.99352}
{"id": 8, "posex": 0.0, "posey": 0.0, "posez": 0.0, "orientx": 0.03362, "orienty": 0.06718, "orientz": -0.08518, "orientw": 0.99353}
{"id": 9, "posex": 0.0, "posey": 0.0, "posez": 0.0, "orientx": 0.03364, "orienty": 0.06718, "orientz": -0.08519, "orientw": 0.99353}
{"id": 10, "posex": 0.0, "posey": 0.0, "posez": 0.0, "orientx": 0.03368, "orienty": 0.06718, "orientz": -0.08519, "orientw": 0.99353}
```

Awesome! I am getting somewhere. Since I am publishing to a topic called `my-topic`, I am getting the data stored in kafka. Time to clean-up and use `quixstreams`! I have been wanting to learn this for a while.

4. Drop the `kafka-producer/producer.py` and `kafka-producer/helper.py` files in the docker container running ROS.



5. Setup a consumer.
