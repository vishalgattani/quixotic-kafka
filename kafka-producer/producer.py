import json

# from helper import get_hostip
import logging
import logging.handlers

# from datetime import datetime
from pprint import pformat

# import time
import rospy
from nav_msgs.msg import Odometry
from quixstreams import Application
from quixstreams.kafka.producer import Producer


def odom_callback(msg, producer: Producer):
    messages = {
        "id": int(msg.header.seq),
        # "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
        "posex": float("{0:.5f}".format(msg.pose.pose.position.x)),
        "posey": float("{0:.5f}".format(msg.pose.pose.position.y)),
        "posez": float("{0:.5f}".format(msg.pose.pose.position.z)),
        "orientx": float("{0:.5f}".format(msg.pose.pose.orientation.x)),
        "orienty": float("{0:.5f}".format(msg.pose.pose.orientation.y)),
        "orientz": float("{0:.5f}".format(msg.pose.pose.orientation.z)),
        "orientw": float("{0:.5f}".format(msg.pose.pose.orientation.w)),
    }

    # Produce the message to Kafka
    producer.produce(
        topic="warty-odom",
        key="odometry",
        value=json.dumps(messages),  # Convert dictionary to JSON string
    )
    logging.debug(f"Produced message: {pformat(messages)}")


def main():
    app = Application(broker_address="localhost:19092", loglevel="DEBUG")
    rospy.init_node("odomSubscriber", anonymous=True)
    try:
        with app.get_producer() as producer:
            # Create a lambda function that includes the producer
            def callback(msg):
                odom_callback(msg, producer)

            # Subscribe to the topic with the new callback
            rospy.Subscriber("warty/odom", Odometry, callback)
            rospy.spin()
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
    finally:
        logging.info("Flushing and closing producer...")


if __name__ == "__main__":
    main()
