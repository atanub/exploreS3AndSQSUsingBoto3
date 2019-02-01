## Overview

Application built on python & boto3 to upload files to AWS-S3.
the Application watches a predefined (configurable) folder in local file system for new files and uploads to S3. S3 & SQS have been used along with Python boto3 to implement this. The application makes use of multi-processing (concurrency) capabilities of python.

## Prerequisites

### Tools

| # | Tools               | Detail                        |
|---|---------------------|-------------------------------|
| 1 | Programing Language | Python 2.7                    |
| 2 | Python Packages     | boto3, botocore, ConfigParser |

### Configuration

Application reads configuration from “Application.properties” during start-up. Configure the below mandatory keys to get started. The key names are self-explanatory. 

| # | Configuration Key | Example Value                           | Type                  | Remarks                                                                                                                                         |
|---|-------------------|-----------------------------------------|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | aws_s3_bucket     | test_bucket                             | Mandatory, Must exist | application doesn’t try to create S3 bucket if not already present. In absence given S3 bucket, the application will crash.                     |
| 2 | aws_s3_folder     | corporate_it/atanu.banik/s3uploaderTest | Mandatory             | N/A                                                                                                                                             |
| 3 | aws_access_key_id | XXXXXXXX                                | Optional              | Access & Secret Keys are optional. Logged in user’s credential will be used if kept empty.                                                      |
| 4 | aws_secret_key    | XXXXXXXX                                | Optional              | Access & Secret Keys are optional. Logged in user’s credential will be used if kept empty.                                                      |
| 5 | aws_region        | us-west-2                               | Mandatory             | N/A                                                                                                                                             |
| 6 | aws_sqs           | atanu_banik                             | Mandatory             | Application tries to create SQS if not present. But it requires admin privileges for SQS service in absence of this the application will crash. |

## How to run?

Execute **main.py** using Python 2.7 interpreter e.g. "C:\Python27\python.exe **main.py**"

```bat
C:\Python27\python.exe main.py
```

### upload files

During start-up, application creates the below sub-folders under the root folder of “main.py”. The folder relative to the root folder of “main.py” can be set by configuration key: ‘folderToStoreTempFiles’.

| # | Folder           | Remarks                                                                                                                                                                                                                                        |
|---|------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | Watch            | A dedicated thread (multi-process in py) monitors this folder for new files. New files are picked up for S3-Upload and moved to the next folder named 'QueuedForUpload'. And it also queues the request for S3-Upload in a local shared queue. |
| 2 | QueuedForUpload  | A dedicated thread consumes files from the local queue and uploads the file to S3. Upon successful upload the S3Key of uploaded file is queued in SQS for other applications to download.                                                      |
| 3 | UploadedToS3     | Upon successful file upload to S3, the candidate files are moved to this folder.                                                                                                                                                               |
| 4 | DownloadedFromS3 | A dedicated thread consumes messages from SQS & downloads the files from S3 to this folder.                                                                                                                                                    |
