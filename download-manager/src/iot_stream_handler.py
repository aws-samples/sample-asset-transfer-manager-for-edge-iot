import os
import sys
import traceback
import json


from awsiot.greengrasscoreipc.model import (QOS, IoTCoreMessage)
from src.job_handler import process_job_document

# This class handles streams from IPC. It is used in main class to subscribe topics.
# The implementation can be found here : https://docs.aws.amazon.com/greengrass/v2/developerguide/interprocess-communication.html

qos = QOS.AT_LEAST_ONCE


class StreamHandler():
    thing_name = ""
    ipc_client = None
    download_in_progress = False

    def __init__(self,  ipc_client):
        self.thing_name = os.environ['AWS_IOT_THING_NAME']
        self.ipc_client = ipc_client
        super().__init__()

    def list_all_jobs(self):
        try:
            print("Listing all jobs ->")
            self.ipc_client.publish_to_iot_core(
                topic_name=f"$aws/things/{self.thing_name}/jobs/get", qos=qos, payload="{}")
        except Exception:
            print('Exception occurred on_stream_event.', file=sys.stderr)
            traceback.print_exc()
            self.ipc_client.close()
            exit(1)

    # This method is called when there is an MQTT payload from the cloud
    def on_stream_event(self, event: IoTCoreMessage) -> None:
        try:
            message = str(event.message.payload, "utf-8")
            topic_name = event.message.topic_name
            print(f"\n{topic_name} -- {message}\n")
            fields = topic_name.split("/")
            payload = json.loads(message)
            if fields[2] == self.thing_name:  # Check if the message addressed to the thing
                # It is a job list event, handle the job list
                if fields[3] == "jobs" and fields[4] == "get" and fields[5] == "accepted":
                    job_list: json = payload["inProgressJobs"] + \
                        payload["queuedJobs"]
                    print(json.dumps(job_list))
                    if (len(job_list) > 0):
                        print(f"found job in list with size = {len(job_list)}")
                        job_id = job_list[0]["jobId"]
                        # get the job details with id of the first "in-progress" if empty "queued" job
                        # considering any resource constraints at edge device we process one job at the time
                        print(f"Describe job with id - {job_id}")
                        self.ipc_client.publish_to_iot_core(
                            topic_name=f"$aws/things/{self.thing_name}/jobs/{job_id}/get", qos=qos, payload=json.dumps({
                                "jobId": job_id,
                                "thingName": self.thing_name,
                            }))
                # It is a job document event, handle the job document
                elif fields[3] == "jobs" and fields[4] != "notify" and fields[5] == "get" and fields[6] == "accepted":
                    job_document = payload["execution"]["jobDocument"]
                    # We need to pass jobId to S3FileDownloader. It will use it to give job progress feedback to Job Manager
                    job_id = payload["execution"]["jobId"]
                    print("It is a job document event, handle the job document ")
                    print(f"{job_id} - {job_document}")
                    process_job_document(self.ipc_client, job_id, job_document)
                    # after processing the job document we get a list of all jobs again to make sure we didn't miss any during offline time
                    self.list_all_jobs()
                 # notify events are called when there is an update to the jobs in IoT Core. For example, when there is a status update on a job.
                elif fields[3] == "jobs" and fields[4] == "notify" and ("IN_PROGRESS" in payload["jobs"] or "QUEUED" in payload["jobs"]):
                    if "IN_PROGRESS" in payload["jobs"]:  # handle job list
                        job_list = payload["jobs"]["IN_PROGRESS"]
                        print(f"job list in progress - {job_list}")
                        # you may use this cancel a job or allow this to continue
                    if "QUEUED" in payload["jobs"]:  # handle job list
                        job_list = payload["jobs"]["QUEUED"]
                        print(f"job list queued - {job_list}")
                        job_id = job_list[0]["jobId"]
                        self.ipc_client.publish_to_iot_core(
                            topic_name=f"$aws/things/{self.thing_name}/jobs/{job_id}/get", qos=qos, payload=json.dumps({
                                "jobId": job_list[0]['jobId'],
                                "thingName": self.thing_name,
                            }))
                        # job_handler.parse_job_list(job_list)
            # When there is a connect/disconnect event in the presence topic, we get the list of jobs again to make sure we didn't miss any during offline time
            # it is a thing connect/disconnect event
            elif fields[2] == "presence" and fields[4] == self.thing_name:
                print("get a list of all jobs")
                self.list_all_jobs()
            else:
                print(f"Unknown message. Skipping. {topic_name} : {message}")

        except Exception:
            print('Exception occurred on_stream_event.', file=sys.stderr)
            traceback.print_exc()
            self.ipc_client.close()
            exit(1)

    def on_stream_error(self, error: Exception) -> bool:
        # Handle error.
        print(error)
        return True  # Return True to close stream, False to keep stream open.

    def on_stream_closed(self) -> None:
        # Handle close.
        print("Stream closed!")
