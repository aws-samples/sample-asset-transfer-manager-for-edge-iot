import json
import os
import sys
import traceback
import boto3
from awsiot.greengrasscoreipc.model import (QOS)

thing_name = os.environ['AWS_IOT_THING_NAME']
qos = QOS.AT_LEAST_ONCE
# S3 client
s3 = boto3.client('s3')
# Download directory comes from component config. This is related to “recipe.yaml” where the command for running this program adds the downloadFolder from the “recipe.yaml” file to the command-line arguments.
args = sys.argv[1:]
# parent_dir is INTENTIONALLY NOT pulled from the Job input parameters so that it CANNOT be over-ridden by someone creating the Job (step[“action”][“ input”][“args”]) to invoke the Component
parent_dir = args[0]


def process_job_document(ipc_client, job_id: str, job_document: json):
    try:
        print(f"processing job document - {job_document}")
        step = job_document["steps"][0]
        if step["action"]["name"] != "Download-File":
            print(f"Job {job_id} for {thing_name} REJECTED")
            ipc_client.publish_to_iot_core(
                topic_name=f"$aws/things/{thing_name}/jobs/{job_id}/update", qos=qos, payload=json.dumps({
                    "status": "REJECTED",
                    "statusDetails": {
                        "status": "unknown action name"
                    }
                }))
        else:
            # update the job status to IN_PROGRESS
            print(f"Job {job_id} for {thing_name} IN_PROGRESS")
            uri: str = step["action"]["input"]["args"][0]
            folder: str = step["action"]["input"]["args"][1]
            ipc_client.publish_to_iot_core(
                topic_name=f"$aws/things/{thing_name}/jobs/{job_id}/update", qos=qos, payload=json.dumps({
                    "status": "IN_PROGRESS",
                    "statusDetails": {
                        "status": "downloading in progress ",
                        "parent_dir": parent_dir,
                        "uri": uri,
                        "folder": folder
                    }
                }))

            # download the file
            status = "SUCCEEDED"

            if not download_file(uri=uri.split("s3://")[1], folder=folder):
                status = "FAILED"

            # mark the job as complete with status
            ipc_client.publish_to_iot_core(
                topic_name=f"$aws/things/{thing_name}/jobs/{job_id}/update", qos=qos, payload=json.dumps({
                    "status": status,
                    "statusDetails": {
                        "uri": uri,
                        "path": folder,
                        "parent_dir": parent_dir,
                    }
                }))

    except Exception:
        print('Exception occurred on_stream_event.', file=sys.stderr)
        # mark the job as failed
        ipc_client.publish_to_iot_core(
            topic_name=f"$aws/things/{thing_name}/jobs/{job_id}/update", qos=qos, payload=json.dumps({
                "status": "FAILED",
                "statusDetails": {
                    "status": "download failed",
                }
            }))
        traceback.print_exc()


def download_file(uri: str, folder: str):
    try:
        # create the folder if it does not exist
        download_path = os.path.join(parent_dir, folder)
        if not os.path.exists(download_path):
            os.makedirs(download_path)
            print(f"download_path - {download_path}")
        # get the bucket name & prefix from the URI
        parts = uri.split("/")
        bucket_name = parts[0]
        # pop the bucket name from the uri parts
        parts.pop(0)
        object_name = "/".join(parts)
        # get the file name from the parts which is the last item in the array
        file_name = parts[-1]
        file_path = os.path.join(download_path, file_name)
        print(f"starting file download - {file_path}")
        if os.path.exists(file_path):
            print(f"overwriting existing file - {file_path}")
        with open(file_path, 'wb') as f:
            s3.download_fileobj(bucket_name, object_name, f)
            print(f"file download completed - {file_path}")
        return True
    except Exception as e:
        print('Exception occurred on_stream_event -- ')
        print(e)
        return False
