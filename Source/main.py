import atexit
import multiprocessing as mp
import os
import time
import traceback
from ApplicationLogger import AppLogger
from ApplicationProperties import applicationConfig
from awsUtil import AwsUtil
import argparse

_logger = AppLogger(__name__).logger


def exit_handler():
    _logger.info('-' * 72)
    _logger.info("Exiting S3FileLoader Process...")
    _logger.info('-' * 72)


atexit.register(exit_handler)


def validateArguments():
    desc = 'Utility for upload/download files to/from S3 from a predefined set of folders.' \
           '\Application monitors a folder for new files. New files are picked up and uploaded to S3. ' \
           '\Upon successful upload, a message gets pushed to SQS for consumer applications to download the file' \
           '\nNOT: This utility process spawns multiple processes which runs forever. ' \
           'The PRE-CONDITION is to kill these sub-processes first.' \
           '\nCommand: ' \
           '\n\t\t\tsudo pkill -f "main"'
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("-Mode", type=int, required=True,
                   help='Execution Mode: ' \
                        '\n   1 = Launch ONLY Producer process;'
                        '\n   2 = Launch ONLY Consumer process;'
                        '\n   3 = Launch both Producer & Consumer in same process;'
                        '\n   4 = Auto-generate test files for continuous upload & download;',
                   )

    p.print_help()
    args = p.parse_args()
    _logger.info("Starting S3FileLoader Service in Mode:%d..." % args.Mode)
    return args.Mode


def start():
    _logger.info('-' * 72)
    _logger.info("Starting S3FileLoader Service...")
    _logger.info('-' * 72)
    queue = mp.Queue()

    executionMode = validateArguments();
    _logger.info("Creating SQS %s if not already available..." % applicationConfig.aws_sqs)
    u = AwsUtil()
    urlSqs = u.createSQS()

    targets = []
    if executionMode & 1:
        # Launch Producer process
        _logger.info("Launching Producer process...")
        targets.append([__watchForFileToUpload, applicationConfig.sleepWatchLocalFolder, queue, executionMode])
        targets.append([__performUpload, applicationConfig.sleepUploadToS3, queue, executionMode])
    if executionMode & 2:
        # Launch Consumer process
        _logger.info("Launching Consumer process...")
        targets.append([__pollSqsAndDownloadFile, applicationConfig.sleepPollSQS, None, executionMode])
    if executionMode & 4:
        _logger.info("Auto-generation of test files for continuous upload & download is enabled...")

    jobs = []
    for target in targets:
        processes = mp.Process(target=target[0], args=(target[1], target[2], target[3]))
        processes.start()
        jobs.append(processes)

    _logger.info("Spawning %d # of processes to execute various tasks concurrently..." % (len(jobs)))

    for job in jobs:
        job.join()

    _logger.info("Exiting S3FileLoader Service....")


def __watchForFileToUpload(sleep_duration, queue, executionMode):
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


def __performUpload(sleep_duration, q, executionMode):
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


def __pollSqsAndDownloadFile(sleep_duration, q, executionMode):
    downloadInWatchFolder = (executionMode & 4) > 0
    while True:
        try:
            print ("Fetching message from SQS to download file from to S3...")
            u = AwsUtil()
            s3Key = u.getSqsMessage(downloadFileFromS3, downloadInWatchFolder)
            print ("Processed message from SQS, Returned Value:%s" % s3Key)
            time.sleep(sleep_duration)
        except Exception as err:
            print("Failed to extract message from SQS!")
            print(str(err))
            print '-' * 72
            traceback.print_exc()
            print '-' * 72


def downloadFileFromS3(s3Key, downloadInWatchFolder):
    u = AwsUtil()
    print ("Downloading file from S3Key:%s..." % (s3Key))
    targetFolder = applicationConfig.folderToWatch if downloadInWatchFolder else applicationConfig.folderForDownloadedFiles
    fileName = None
    if downloadInWatchFolder:
        fileName = getFileNameFromS3Key(s3Key)
        fileName = getNextVersionOfFile(fileName)

    filePath = u.downloadFileFromS3(s3Key, targetFolder, fileName)
    print ("Downloaded File:%s from S3:%s." % (filePath, s3Key))
    return True


def getFileNameFromS3Key(s3Key):
    fileName = s3Key.split("/")
    fileName = fileName[len(fileName) - 1]
    return fileName


def getNextVersionOfFile(fileNameWithoutPath):
    v = "-Version-"
    index = fileNameWithoutPath.rfind(v)
    if index < 0:
        f = "%s%s%d" % (fileNameWithoutPath, v, 1)
        return f
    words = fileNameWithoutPath.split(v)
    vid = int(words[len(words) - 1]) + 1
    words[len(words) - 1] = v
    words.append(str(vid))
    f = "".join(words)
    return f


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
