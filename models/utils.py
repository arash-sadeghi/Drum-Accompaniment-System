import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from models.CONST_VARS import CONST

def print2(s):
    print(f"[+][{__name__}]"+s)

def generator_weight_provider():
    download_file_from_s3(CONST.bucket_name, CONST.s3_file_key, CONST.generator_file_path)


def download_file_from_s3(bucket_name, s3_file_key, file_path):
    """Checks if the file exists locally, if not downloads it from S3."""
    if os.path.exists(file_path):
        print2(f"{file_path} already exists.")
        return

    # Initialize S3 client
    s3 = boto3.client('s3')

    try:
        print2(f"Downloading {s3_file_key} from bucket {bucket_name} to {file_path}...")
        s3.download_file(bucket_name, s3_file_key, file_path)
        print2(f"Downloaded {file_path} successfully.")
    except NoCredentialsError:
        print2("AWS credentials not found.")
    except ClientError as e:
        print2(f"Error downloading file: {e}")

'''
aws s3 mb s3://das.backend 
aws s3 cp /Users/arashsadeghiamjadi/Desktop/WORKDIR/JamBuddy/Server_App/models/generator_weights.pth s3://das.backend/generator_weights.pth
# make sure public access is alowed from console
# allow acls from console
aws s3api put-object-acl --bucket das.backend --key generator_weights.pth --acl public-read
# the url should be https://das.backend.s3.amazonaws.com/generator_weights.pth
# training_output_path_rootgenerator_20000.pth url is   https://das.backend.s3.amazonaws.com/training_output_path_rootgenerator_20000.pth
'''
