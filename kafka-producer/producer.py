import rospy
from nav_msgs.msg import Odometry
import json
from datetime import datetime
from quixstreams import Application
from helper import get_hostip
import logging
from typing import Optional
from pprint import pformat

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class KafkaProducer:
    def __init__(self,topic_name:str):
        self.count = 0
        self.hostip = get_hostip()
        logging.debug(f"Host IP: {self.hostip}")
        self.app = Application(broker_address=f"{self.hostip}:9092", loglevel="INFO")
        self.producer = self.app.get_producer()
        self.topic = topic_name
        self.logger = logging.getLogger(f"{__name__}.KafkaProducer")
        self.logger.info(f"KafkaProducer initialized with topic: {topic_name}")
        
    def odom_callback(self, msg):
            self.count += 1
            # print(msg)
            messages = {
                "id": int(msg.header.seq),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "posex": float("{0:.5f}".format(msg.pose.pose.position.x)),
                "posey": float("{0:.5f}".format(msg.pose.pose.position.y)),
                "posez": float("{0:.5f}".format(msg.pose.pose.position.z)),
                "orientx": float("{0:.5f}".format(msg.pose.pose.orientation.x)),
                "orienty": float("{0:.5f}".format(msg.pose.pose.orientation.y)),
                "orientz": float("{0:.5f}".format(msg.pose.pose.orientation.z)),
                "orientw": float("{0:.5f}".format(msg.pose.pose.orientation.w))
            }
            
            print(f"Producing message: {pformat(messages)}")
            rospy.logdebug(f"ROS Debug: Producing message: {messages}")  # ROS-specific logging
            self.producer.produce(
                topic=self.topic,
                key="odometry",
                value=json.dumps(messages)
            )
            

    def run(self,subscriber_node_name:str,topic_name:str,msg_type:Optional[type]=None):
        try:
            rospy.init_node(f'{subscriber_node_name}', anonymous=True)
            rospy.Subscriber(f'{topic_name}', Odometry, self.odom_callback)
            self.logger.info(f"Subscriber node '{subscriber_node_name}' started. Listening on topic: {topic_name}")
            rospy.loginfo(f"ROS Info: Subscriber node '{subscriber_node_name}' started. Listening on topic: {topic_name}")
            rospy.spin()
        except rospy.ROSInterruptException:
            self.logger.error("ROS Node Interrupted")
        except KeyboardInterrupt:
            self.logger.info("Keyboard Interrupt received. Shutting down...")
        except Exception as e:
            self.logger.exception(f"Unexpected error: {e}")
        finally:
            self.producer.flush()
            self.logger.info("Producer flushed. Shutting down.")

if __name__ == "__main__":
    try:
        logging.info("START")
        producer = KafkaProducer(topic_name="warty-odom")
        producer.run(subscriber_node_name="odom_subscriber",topic_name="warty/odom",msg_type=Odometry)
    except rospy.ROSInterruptException:
        logging.error("ROS Node Interrupted")
    except KeyboardInterrupt:
        logging.info("Keyboard Interrupt received. Shutting down...")
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
    finally:
        producer.producer.flush()
        logging.info("Producer flushed. Shutting down.")