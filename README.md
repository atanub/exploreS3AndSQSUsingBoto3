Sample Application to watch a folder in local file system and upload/download to/from S3. S3 & SQS have been used along with Python boto3 to implement this. The application also makes use of multi-processing (concurrency) capabilities of python. 
1.	Prerequisites:
1.1.	The application requires Python 2.7 and packages [boto3, botocore, ConfigParser]
2.	Configuration:
3.	Application reads configurations from “Application.properties” at during start-up. Configure the below mandatory keys to get started. The key names are self-explanatory. 
3.1.	[Mandatory, Must exist]	aws_s3_bucket=test_bucket
3.2.	[Mandatory]		aws_s3_folder=corporate_it/atanu.banik/s3uploaderTest
3.3.	[Optional]			aws_access_key_id=XXXXXXXX
3.4.	[Optional]			aws_secret_key= XXXXXXXX
3.5.	[Mandatory]		aws_region=us-west-2
3.6.	[Mandatory]		aws_sqs=atanu_banik

4.	Application tries to create SQS if not present. But it requires admin privileges for SQS service in absence of this the application will crash.
5.	But application doesn’t try to create S3 bucket if not already present. In absence given S3 bucket, the application will crash.
6.	Access & Secret Keys are optional. Logged in user’s credential will be used if kept empty.

7.	How to run?
7.1.	Run main.py using Python 2.7 interpreter e.g. "C:\Python27\python.exe main.py"

8.	How to upload files?
During start-up application creates the below sub-folders under the root folder of “main.py”. The folder relative to the root folder of “main.py” can be set by configuration key: ‘folderToStoreTempFiles’.

8.1.	Watch
A dedicated thread (multi-process in py) monitors this folder for new files. New files are picked up for S3-Upload and moved to the next folder named 'QueuedForUpload'. And it also queues the request for S3-Upload in a local shared queue.
8.2.	QueuedForUpload
A dedicated thread consumes files from the local queue and uploads the file to S3. Upon successful upload the S3Key of uploaded file is queued in SQS for other applications to download.
8.3.	UploadedToS3
Upon successful file upload to S3, the candidate files are moved to this folder.
8.4.	DownloadedFromS3
A dedicated thread consumes messages from SQS & downloads the files from S3 to this folder.
