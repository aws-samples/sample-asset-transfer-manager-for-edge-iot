import sys
import os
import sys
import traceback
import threading

import awsiot.greengrasscoreipc.clientv2 as clientV2
from awsiot.greengrasscoreipc.model import (QOS)

# custom classes
import src.iot_stream_handler as iot_stream_handler

ipc_client = clientV2.GreengrassCoreIPCClientV2()
qos = QOS.AT_LEAST_ONCE

thing_name = os.environ['AWS_IOT_THING_NAME']

# Subscribe to AWS IoT Core MQTT topics
#
topics = [f"$aws/things/{thing_name}/jobs/notify",  # IoT job topic to receive job updates
          # IoT job topic to receive job list
          f"$aws/things/{thing_name}/jobs/get/accepted",
          # IoT job topic to receive job document
          f"$aws/things/{thing_name}/jobs/+/get/accepted",
          # Job update accepted/rejected
          f"$aws/things/{thing_name}/jobs/+/update/#",
          # AWS IoT Core sends presence update events to this topic. It is used to get the latest job list in case of connection disruption.
          f"$aws/events/presence/+/{thing_name}"
          ]


def main():
    try:
        handler = iot_stream_handler.StreamHandler(ipc_client)
        # Subscribe IoT Core MQTT topics
        for topic in topics:
            print(f"subscribing to {topic}")

            resp = ipc_client.subscribe_to_iot_core(
                topic_name=topic,
                qos=qos,
                on_stream_event=handler.on_stream_event,
                on_stream_error=handler.on_stream_error,
                on_stream_closed=handler.on_stream_closed
            )

            print(f"subscription to {topic} success with message - {resp}")

        # get all pending jobs
        handler.list_all_jobs()

        # Keep the main thread alive, or the process will exit.
        event = threading.Event()
        event.wait()

    except Exception:
        print('Exception occurred when using IPC.', file=sys.stderr)
        traceback.print_exc()
        #  IPC Client close the connection
        ipc_client.close()
        exit(1)


if __name__ == "__main__":
    main()
