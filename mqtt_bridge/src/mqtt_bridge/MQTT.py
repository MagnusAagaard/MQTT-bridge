import paho.mqtt.client as mqtt
from six.moves import urllib
import time
from collections import deque
import rospy

robot_status = 1;               #initialize status as free
robot_currentRoom = "";         #no room has been granted the robot yet
robot_queue = deque();          #queue empty

def mqtt_server_node():
    # init node
    rospy.init_node('mqtt_server_node')
    client = mqtt.Client();
    client.on_connect = on_connect;
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.connect("10.0.2.15", 1883, 60);
    print("started")
    # start MQTT loop
    client.loop_start()

    # register shutdown callback and spin
    rospy.on_shutdown(client.disconnect)
    rospy.on_shutdown(client.loop_stop)
    rospy.spin()

def on_disconnect(client, userdata, rc):
    rospy.loginfo('MQTT2 disconnected')

def on_connect(client, userdata, flags, rc):
    #print("Connected with result code "+str(rc));
    client.subscribe([("cancelTopic" ,1), ("requestStatus",1), ("requestRobot",1), ("testTopic",1)]); #subscribe to topics
    sendString = "{"+'"'+"data"+'"'+':'+'"'+"helloFrompyth"+'"'+"}"
    print(sendString)
    client.publish("echo",sendString)

def on_message(client, userdata, msg):
    #message = str(msg.payload).split("'")[1];   #make payload to a string
    print("message recieved: "+msg.topic+" "+msg.payload);
    
    global robot_status;
    global robot_currentRoom;
    global robot_queue;
    
    if msg.topic == 'requestStatus':
        if robot_status == 1:
            client.publish("buttonsInTopic", "1");
        elif robot_status == 2:
            client.publish("buttonsInTopic", "2"+robot_currentRoom);     #if status is 2 (robot granted), send the ID of the granted room as well
            
    elif msg.topic == 'cancelTopic':         #Cancel is called - cancel can only be called from the button that has been granted the robot
        if robot_status == 2:       #check if status is 2 (robot granted to a room)
            if len(robot_queue)>0:      #if there is anyone in the queue, grant them the robot
                robot_status = 2;
                robot_currentRoom = robot_queue.popleft();   #first in queue gets the robot
                print("Length of the queue is now: "+str(len(robot_queue)))
                client.publish("buttonsInTopic", "2"+robot_currentRoom);
            else:
                print("Robot was cancelled and no one in queue");
                robot_status = 1;
                client.publish("buttonsInTopic", "1");
        else :
            print("Cancel was called, but status is not 2");
            sendString = "{"+'"'+"data"+'"'+':'+'"'+"helloFrompythonCancel"+'"'+"}"
            client.publish("echo",sendString)
                
    elif msg.topic == 'requestRobot':
        if robot_status == 1:
            robot_status = 2;                   #grant the robot
            robot_currentRoom = message;        #when a button requests the robot, the room ID for the button is the payload
            client.publish("buttonsInTopic", "2"+robot_currentRoom);
            print("requestRobot and status was 1, publishing 2 and roomID to buttonsInTopic")
        else :
            if robot_queue.count(message) == 0:         #if the button is not already in queue, add it
                print("Adding: "+message+" to the queue");
                robot_queue.append(message);
                print("Length of queue is now: "+str(len(robot_queue)));
            else :
                print("Button is already in queue..");
                #client.publish("cancelTopic", "cancel");

    else :
        print("The topic recieved was not one I had to react on");
        
    return;

__all__ = ['mqtt_server_node']

