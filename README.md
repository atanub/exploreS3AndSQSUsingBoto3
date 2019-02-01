## Overview

Application built using python & boto3 to upload files to AWS-S3.
* Application watches a predefined (configurable) folder in local file system for new files to arrive. Upon detecting new file it uploads to S3.
* AWS S3 and AWS SQS are used along with Python boto3 to implement this.
* The application makes use of multi-processing (concurrency) capabilities of python.

### Architecture
![Architecture](Document/Architecture,&#32;Design&#32;and&#32;Data&#32;Flow&#32;Diagram.png)

## Prerequisites

### Tools

| # | Tools               | Detail                        |
|---|---------------------|-------------------------------|
| 1 | Programing Language | Python 2.7                    |
| 2 | Python Packages     | boto3, botocore, ConfigParser |

### Configuration

Application reads configuration from [Application.properties](Source/Application.properties) during start-up. Configure the below mandatory keys to get started. The key names are self-explanatory.

| # | Key | Example Value                           | Type                  | Remarks                                                                                                                                         |
|---|-------------------|-----------------------------------------|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | aws_s3_bucket     | test_bucket                             | Mandatory | application doesn’t try to create S3 bucket if not already present. In absence of S3 bucket, the application crashes.                     |
| 2 | aws_s3_folder     | corporate_it/atanu.banik/s3uploaderTest | Mandatory             | N/A                                                                                                                                             |
| 3 | aws_access_key_id | XXXXXXXX                                | Optional              | Access & Secret Keys are optional. Logged in user’s credential will be used if kept empty.                                                      |
| 4 | aws_secret_key    | XXXXXXXX                                | Optional              | Access & Secret Keys are optional. Logged in user’s credential will be used if kept empty.                                                      |
| 5 | aws_region        | us-west-2                               | Mandatory             | N/A                                                                                                                                             |
| 6 | aws_sqs           | atanu_banik                             | Mandatory             | Application tries to create SQS if not present. It requires admin privileges for creating SQS service. Application crashes in absence of SQS or admin privileges to create SQS. |

## How to run?

Execute [main.py](Source/main.py) using Python 2.7 interpreter e.g. "C:\Python27\python.exe [main.py](Source/main.py)"

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
