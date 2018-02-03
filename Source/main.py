import atexit
import multiprocessing as mp
import os
import time
import traceback
from ApplicationLogger import AppLogger
from ApplicationProperties import applicationConfig
from awsUtil import AwsUtil

_logger = AppLogger(__name__).logger


def exit_handler():
    _logger.info('-' * 72)
    _logger.info("Exiting S3FileLoader Process...")
    _logger.info('-' * 72)


atexit.register(exit_handler)


def start():
    _logger.info('-' * 72)
    _logger.info("Starting S3FileLoader Service...")
    _logger.info('-' * 72)
    queue = mp.Queue()

    _logger.info("Creating SQS %s if not already available..." % applicationConfig.aws_sqs)
    u = AwsUtil()
    urlSqs = u.createSQS()

    targets = (
        [__watchForFileToUpload, applicationConfig.sleepWatchLocalFolder, queue],
        [__performUpload, applicationConfig.sleepUploadToS3, queue],
        [__pollSqsAndDownloadFile, applicationConfig.sleepPollSQS, None]
    )
    jobs = []
    for target in targets:
        processes = mp.Process(target=target[0], args=(target[1], target[2]))
        processes.start()
        jobs.append(processes)

    _logger.info("Spawning %d # of processes to execute various tasks concurrently..." % (len(jobs)))

    for job in jobs:
        job.join()

    _logger.info("Exiting S3FileLoader Service....")


def __watchForFileToUpload(sleep_duration, queue):
    folderRoot = applicationConfig.folderToWatch
    folderQueued = applicationConfig.folderQueuedForUpload

    print  ("Watching files for copy in folder:%s..." % (folderRoot))

    while True:
        print("Watching files for copy in folder:%s..." % (folderRoot))
        files = pickFilesAndMoveToQueueFolder(folderRoot, folderQueued)
        if len(files) > 0:
            print ("Found %d # of files for upload..." % (len(files)))
            [queue.put(f) for f in files]
        time.sleep(sleep_duration)


def __performUpload(sleep_duration, q):
    while True:
        try:
            if q.qsize() > 0:
                o = q.get()
                uploadToS3AndEnqueInSQS(o)
            else:
                print("No File found for upload.")

            time.sleep(sleep_duration)
        except Exception as err:
            print("Failed to determine file for upload!")
            print(str(err))
            print '-' * 72
            traceback.print_exc()
            print '-' * 72


def __pollSqsAndDownloadFile(sleep_duration, q):
    while True:
        try:
            print ("Fetching message from SQS to download file from to S3...")
            u = AwsUtil()
            s3Key = u.getSqsMessage(downloadFileFromS3)
            print ("Processed message from SQS, Returned Value:%s" % s3Key)
            time.sleep(sleep_duration)
        except Exception as err:
            print("Failed to extract message from SQS!")
            print(str(err))
            print '-' * 72
            traceback.print_exc()
            print '-' * 72


def downloadFileFromS3(s3Key):
    u = AwsUtil()
    print ("Downloading file from S3Key:%s..." % (s3Key))
    filePath = u.downloadFileFromS3(s3Key, applicationConfig.folderForDownloadedFiles)
    print ("Downloaded File:%s from S3:%s." % (filePath, s3Key))
    return True


def uploadToS3AndEnqueInSQS(filePath):
    u = AwsUtil()
    print ("Uploading File:%s to S3..." % (filePath))
    fileIdInS3 = u.uploadFileToS3(filePath)
    if fileIdInS3 == None:
        print ("Failed to Upload File:%s to S3." % (filePath))
        return

    print ("Uploaded File:%s to S3." % (filePath))
    messageId = u.sendSqsMessage(fileIdInS3)
    print ("Message Queued for Upload notification to SQS for File:%s, SQS Message ID:%s." % (fileIdInS3, messageId))
    filePathMoved = os.path.join(applicationConfig.folderForUploadedFiles, os.path.basename(filePath))
    os.rename(filePath, filePathMoved)


def pickFilesAndMoveToQueueFolder(folderRoot, folderQueued):
    files = [os.path.join(folderRoot, name) for name in os.listdir(folderRoot) if
             os.path.isfile(os.path.join(folderRoot, name))]

    funcs = [lambda x: x, lambda x: ("%s/%s" % (folderQueued, os.path.basename(x)))]
    ff = list(map(lambda x: {'Source': x, 'Target': ("%s/%s" % (folderQueued, os.path.basename(x)))}, files))
    for f in ff:
        os.rename(f["Source"], f["Target"])

    fff = list(map(lambda x: x["Target"], ff))
    return fff


if __name__ == '__main__':
    start()
