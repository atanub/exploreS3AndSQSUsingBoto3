import os
import traceback
import boto3
import botocore
from ApplicationLogger import AppLogger


class AwsUtil:
    def __init__(self):
        from ApplicationProperties import applicationConfig

        self._config = applicationConfig
        self._bucket = self._config.aws_s3_bucket
        self._s3KeyPrefix = self._config.aws_s3_folder
        self._queueName = self._config.aws_sqs
        self._region = self._config.aws_region

        self._sqsUrl = None
        self._sqsUrl = self.createSQS()
        pass

    def __logException(self, message, exception):
        print message
        l = AppLogger(__name__).logger
        l.error(message)
        if exception != None:
            print str(exception)
            l.error(str(exception))

    def __logError(self, message):
        self.__logException(message, None)

    def __logInfo(self, message):
        print message
        l = AppLogger(__name__).logger
        l.info(message)

    def uploadFileToS3(self, localFilePath):
        try:
            s3 = self._getS3Client()
            fileName = os.path.basename(localFilePath)
            key = "%s/%s" % (self._s3KeyPrefix, fileName)
            response = s3.meta.client.upload_file(localFilePath, self._bucket, key)
            # with open(localFilePath, 'rb') as data:
            #     response = s3.upload_fileobj(data, self._bucket, key)
            return key
        except Exception, e:
            self.__logException("Exception occurred while uploading file:%s to S3!" % localFilePath, str(e))
            print '-' * 72
            traceback.print_exc()
            print '-' * 72

        return None

    def downloadFileFromS3(self, s3Key, outputFolderPath, fileName):
        filePath = None
        if fileName:
            filePath = self.getFilePathForDownload(fileName, outputFolderPath)
        else:
            filePath = self.getFilePathForDownload(s3Key, outputFolderPath)

        try:
            s3 = self._getS3Client()
            s3.meta.client.download_file(self._bucket, s3Key, filePath)
            return filePath
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                self.__logException(
                    "Failed to download file from S3, Bucket:%s Key:%s! File not found!" % (self._bucket, s3Key),
                    str(e))
            else:
                raise
        return None

    def getFilePathForDownload(self, s3Key, localFolderName):
        fileName = s3Key.split("/")
        fileName = fileName[len(fileName) - 1]
        filePath = os.path.join(localFolderName, fileName)
        return filePath

    def createSQS(self):
        if self._sqsUrl != None and len(self._sqsUrl) > 0:
            return self._sqsUrl

        self._sqsUrl = self.isSqsResourceExists()
        if self._sqsUrl != None and len(self._sqsUrl) > 0:
            return self._sqsUrl
        try:
            sqs = self._getSqsClient()
            response = sqs.create_queue(
                QueueName=self._queueName
            )
            self._sqsUrl = response["QueueUrls"][0]
            self.__logInfo('SQS Queue "%s" has been created successfully' % self._sqsUrl)
            return self._sqsUrl
        except Exception as err:
            self.__logException("Failed to create SQS: '%s' in region: '%s'!" % (self._queueName, self._region),
                                str(err))
            print '-' * 72
            traceback.print_exc()
            print '-' * 72
        return None

    def isSqsResourceExists(self):
        if self._sqsUrl != None and len(self._sqsUrl) > 0:
            return True

        try:
            sqs = self._getSqsClient()
            response = sqs.list_queues(
                QueueNamePrefix=self._queueName
            )
            return response["QueueUrls"][0]
        except Exception as err:
            self.__logException("SQS:'%s' doesn't exist in region: '%s'!" % (self._queueName, self._region), str(err))
            print '-' * 72
            traceback.print_exc()
            print '-' * 72

        return None

    def sendSqsMessage(self, message):
        if self._sqsUrl == None or len(self._sqsUrl) <= 0:
            self.__logError("Failed to send message '%s' to SQS, SQS was never initialized!" % (message))
            return None

        try:
            sqs = self._getSqsClient()
            response = sqs.send_message(QueueUrl=self._sqsUrl, MessageBody=message)
            self.__logInfo('Message ID : %s' % response['MessageId'])
            return response['MessageId']
        except Exception as err:
            self.__logException("Failed to send message '%s' to SQS '%s'!" % (message, self._sqsUrl), str(err))
            print '-' * 72
            traceback.print_exc()
            print '-' * 72

        return None

    def getSqsMessage(self, messageHandler, downloadInWatchFolder):
        if self._sqsUrl == None or len(self._sqsUrl) <= 0:
            self.__logError("Failed to get message from SQS, SQS was never initialized!")
            return None

        try:
            sqs = self._getSqsClient()
            response = sqs.receive_message(
                QueueUrl=self._sqsUrl,
                AttributeNames=['SentTimestamp'],
                MaxNumberOfMessages=1,
                MessageAttributeNames=['All'],
                VisibilityTimeout=0,
                WaitTimeSeconds=0
            )
            s3BucketAndKey = None
            receipt_handle = None
            if ('Messages' in response):
                message = response['Messages'][0]
                if ('Body' in message):
                    s3BucketAndKey = message['Body']
                receipt_handle = message['ReceiptHandle']
            else:
                self.__logInfo('No SQS Message found...')
                return None

            if s3BucketAndKey != None:
                self.__logInfo('Calling SQS Message handler for message: %s...' % s3BucketAndKey)
                if not messageHandler(s3BucketAndKey, downloadInWatchFolder):
                    self.__logError('SQS Message handler failed to process message: %s!' % s3BucketAndKey)
                    return None
                self.__logInfo('SQS Message handler execution completed for message: %s...' % s3BucketAndKey)

            self.__logInfo('Deleting received Message "%s" from SQS: %s...' % (s3BucketAndKey, self._sqsUrl))
            # Delete received message from queue
            sqs.delete_message(
                QueueUrl=self._sqsUrl,
                ReceiptHandle=receipt_handle
            )
            self.__logInfo('Deleted received Message "%s" from SQS: %s' % (s3BucketAndKey, self._sqsUrl))
            return s3BucketAndKey
        except Exception as err:
            self.__logException("Failed to extract from SQS '%s'!" % (self._sqsUrl), str(err))
            print '-' * 72
            traceback.print_exc()
            print '-' * 72

        return None

    def _getSqsClient(self):
        try:
            b = self._config.aws_secret_key != None and len(self._config.aws_secret_key) > 0
            b = b and self._config.aws_access_key_id != None and len(self._config.aws_access_key_id) > 0
            if not b:
                sqs = boto3.client('sqs', region_name=self._region)
            else:
                sqs = boto3.client('sqs', region_name=self._region, aws_access_key_id=self._config.aws_access_key_id,
                                   aws_secret_access_key=self._config.aws_secret_key)

            return sqs
        except Exception as err:
            self.__logException("Failed to create SQS client!", str(err))
            print '-' * 72
            traceback.print_exc()
            print '-' * 72

        return None

    def _getS3Client(self):
        try:
            b = self._config.aws_secret_key != None and len(self._config.aws_secret_key) > 0
            b = b and self._config.aws_access_key_id != None and len(self._config.aws_access_key_id) > 0
            if not b:
                s3 = boto3.resource('s3', region_name=self._region)
            else:
                s3 = boto3.resource('s3', region_name=self._region, aws_access_key_id=self._config.aws_access_key_id,
                                    aws_secret_access_key=self._config.aws_secret_key)

            return s3
        except Exception as err:
            self.__logException("Failed to create SQS client!", str(err))
            print '-' * 72
            traceback.print_exc()
            print '-' * 72

        return None


if __name__ == '__main__':
    # for Unit Test ONLY ###############################################
    from ApplicationProperties import applicationConfig

    util = AwsUtil()
    localFilePath = "C:/Temp/S3FileLoader/Queued/1 (1).json"
    util.uploadFileToS3(localFilePath)

    url = util.isSqsResourceExists()
    url = util.createSQS()
    messageId = util.sendSqsMessage("atanu.banik/test")
    print messageId
    message = util.getSqsMessage()
    print message
