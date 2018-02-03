import traceback
import os, sys
import ConfigParser


class ApplicationProperties():
    def __init__(self):
        path = os.path.abspath(__file__)
        self.__moduleRootFolder = os.path.dirname(os.path.dirname(path))
        self.__fileName = 'Application.properties'
        print "Reading Application Configuration from file:" + self.__fileName
        self.parent_dir = os.path.dirname(os.path.abspath(__file__))
        self.parent_dir = os.path.dirname(os.path.abspath(__file__))
        self.propertiesFilepath = os.path.join(self.parent_dir, self.__fileName)
        self.__readConfigFile(self.propertiesFilepath)

    def __setupTemporaryFolder(self, folderPathRelative):
        try:
            path = os.path.abspath(__file__)
            path = os.path.dirname(path)
            tempFolderPath = os.path.join(path, folderPathRelative)
            if not os.path.exists(tempFolderPath):
                os.makedirs(tempFolderPath)

            return tempFolderPath
        except Exception as err:
            print("FATAL ERROR: Failed to setup TEMP folder within Module Root, encountered exception!")
            print(str(err))
            print '-' * 72
            traceback.print_exc()
            print '-' * 72

        return None

    def __readConfigFile(self, cfg):
        try:
            config = ConfigParser.ConfigParser()
            config.read(cfg)

            self.folderToStoreTempFiles = config.get('General', 'folderToStoreTempFiles').strip()
            self.folderToWatch = config.get('General', 'folderToWatch').strip()
            self.folderQueuedForUpload = config.get('General', 'folderQueuedForUpload').strip()
            self.folderForUploadedFiles = config.get('General', 'folderForUploadedFiles').strip()
            self.folderForDownloadedFiles = config.get('General', 'folderForDownloadedFiles').strip()

            ####
            self.folderToStoreTempFiles = self.__setupTemporaryFolder(self.folderToStoreTempFiles)
            self.folderToWatch = os.path.join(self.folderToStoreTempFiles, self.folderToWatch)
            self.folderForUploadedFiles = os.path.join(self.folderToStoreTempFiles, self.folderForUploadedFiles)
            self.folderQueuedForUpload = os.path.join(self.folderToStoreTempFiles, self.folderQueuedForUpload)
            self.folderForDownloadedFiles = os.path.join(self.folderToStoreTempFiles, self.folderForDownloadedFiles)

            foldersToCreate = [self.folderToWatch, self.folderForUploadedFiles, self.folderQueuedForUpload,
                               self.folderForDownloadedFiles]

            for f in foldersToCreate:
                if not os.path.exists(f):
                    os.makedirs(f)

            self.logFilePath = config.get('General', 'logFilePath').strip()
            self.logFilePath = os.path.join(self.folderToStoreTempFiles, self.logFilePath)

            self.sleepWatchLocalFolder = float(config.get('Concurrency', 'sleepWatchLocalFolder'))
            self.sleepUploadToS3 = float(config.get('Concurrency', 'sleepUploadToS3'))
            self.sleepPollSQS = float(config.get('Concurrency', 'sleepPollSQS'))

            self.automaticFileUploadEnabled = int(config.get('Environment', 'operationMode')) > 0

            self.aws_s3_bucket = config.get('AWS', 'aws_s3_bucket').strip()
            self.aws_access_key_id = config.get('AWS', 'aws_access_key_id').strip()
            self.aws_secret_key = config.get('AWS', 'aws_secret_key').strip()
            self.aws_region = config.get('AWS', 'aws_region').strip()
            self.aws_sqs = config.get('AWS', 'aws_sqs').strip()
            self.aws_s3_folder = config.get('AWS', 'aws_s3_folder').strip()

        except Exception as err:
            print("FATAL ERROR: Failed to read application property file: " + cfg)
            print '-' * 72
            traceback.print_exc()
            print '-' * 72


applicationConfig = ApplicationProperties()
