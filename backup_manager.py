import argparse
import datetime
import os
import tarfile
import boto3
import sys

def get_timestamp():
    """
    Returns the current date and time in a human-readable string format for file naming.
    """
    return datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

def rename_folder_with_snapshot(folder_path):
    # Check if the folder exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        # Get the current date and time in string format
        date_str = get_timestamp()
        # Create the new folder name
        base_folder_name = os.path.basename(folder_path.rstrip('/\\'))
        parent_folder = os.path.dirname(folder_path)
        new_folder_name = os.path.join(parent_folder, f"{base_folder_name}_snapshot_{date_str}")
        # Rename the folder
        os.rename(folder_path, new_folder_name)
        print(f"Existing folder {folder_path} renamed to: {new_folder_name}")
    else:
        print(f"Folder '{folder_path}' does not exist.")

def create_tarfile(source_dir, output_filename):
    """
    Compresses the given directory into a tar.gz file.
    """
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

def extract_tarfile(input_tarfile, target_dir):
    """
    Extracts a tar.gz file into the specified directory.
    """
    with tarfile.open(input_tarfile, "r:gz") as tar:
        tar.extractall(path=target_dir)
        
def delete_tarfile(tar_filename, verify=False):
    """
    Deletes the specified tar.gz file.
    """
    
    # Verify before deleting
    if verify:
        print(f"Ready to delete local tar file {tar_filename}. Continue? [y/n]: ", end='')
        if input().lower() != 'y':
            print("tar deletion aborted by the user.")
            return
    else:
        print(f"Ready to delete local tar file {tar_filename}.")

    if os.path.exists(tar_filename):
        os.remove(tar_filename)
        print(f"{tar_filename} has been deleted locally.")
    else:
        print(f"{tar_filename} does not exist.")

def list_bucket_objects(bucket_name, s3_client):
    """
    List all objects in the specified S3 bucket.
    """
    try:
        objects = s3_client.list_objects_v2(Bucket=bucket_name)['Contents']
        if objects:
            print("The following files are present in the bucket:")
            for obj in objects:
                print(f"- {obj['Key']} ({obj['LastModified']})")
        return objects
    except KeyError:
        return []  # No content in bucket
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)

def cleanup_snapshots(bucket_name, s3_client, keep=3, verify=False):
    """
    Retains only the latest 'keep' snapshots in the bucket and deletes the rest.
    If verify is True, it prompts the user before deletion.
    """
    objects = list_bucket_objects(bucket_name, s3_client)
    sorted_objects = sorted(objects, key=lambda obj: obj['LastModified'], reverse=True)

    # Identify objects to delete
    objects_to_delete = sorted_objects[keep:]

    if objects_to_delete:
        print("The following files will be deleted from the bucket:")
        for obj in objects_to_delete:
            print(f"- {obj['Key']} ({obj['LastModified']})")
    else:
        print("No files to delete.")
            
    if verify:
        if objects_to_delete:
            # Ask for confirmation
            print("Do you want to continue with the deletion? [y/n]: ", end='')
            user_input = input().lower()
            if user_input != 'y':
                print("Deletion aborted by the user.")
                return

    # Proceed with deletion
    for obj in objects_to_delete:
        s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
        print(f"Deleted {obj['Key']}")

def upload_file_to_s3(file_name, bucket_name, object_name, s3_client):
    """
    Uploads a file to an S3 bucket.
    """
    try:
        response = s3_client.upload_file(file_name, bucket_name, object_name)
    except Exception as e:
        print(f"Failed to upload {file_name} to {bucket_name}/{object_name}: {e}")
        return False
    return True

def download_file_from_s3(bucket_name, object_name, file_name, s3_client):
    """
    Downloads a file from an S3 bucket.
    """
    try:
        s3_client.download_file(bucket_name, object_name, file_name)
        print(f"Downloaded {object_name} from {bucket_name}")
    except Exception as e:
        print(f"Failed to download {object_name} from {bucket_name}: {e}")
        return False
    return True

def setup_arg_parser():
    """
    Sets up command line argument parsing.
    """
    parser = argparse.ArgumentParser(description="Manage backups with AWS S3.")
    parser.add_argument("--verify", action="store_true", help="Enable verification before proceeding with any changes.")
    parser.add_argument("action", choices=["backup", "restore"], help="The action to perform: 'backup' or 'restore'.")
    parser.add_argument("folder_path", help="The folder to 'backup' or 'restore'.")
    parser.add_argument("folder_name", help="The name of the folder to 'backup' or 'restore'.")
    return parser

if __name__ == "__main__":
    print(f"Invoked with arguments: {sys.argv[1:]}")
    
    parser = setup_arg_parser()
    args = parser.parse_args()

    # Configuration and AWS S3 Client setup
    bucket_name = os.environ.get("AWS_BUCKET_NAME")
    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    
    s3_client = boto3.client('s3',
        aws_access_key_id = aws_access_key_id,
        aws_secret_access_key = aws_secret_access_key)
    
    folder_path = args.folder_path
    folder_name = args.folder_name
    print(f"Processing path {folder_path}, folder {folder_name}")

    if args.action == "backup":
        # Compress the folder
        timestamp = get_timestamp()
        tar_filename = f"{folder_name}-snapshot-{timestamp}.tar.gz"
        create_tarfile(folder_path, tar_filename)

        # Verify before uploading
        if args.verify:
            print(f"Ready to upload {tar_filename} to {bucket_name}. Continue? [y/n]: ", end='')
            if input().lower() != 'y':
                print("Aborting operation.")
                sys.exit(1)
        else:
            print(f"Ready to upload {tar_filename} to {bucket_name}.")

        # Upload the file
        if upload_file_to_s3(tar_filename, bucket_name, tar_filename, s3_client):
            print("Upload successful.")
            cleanup_snapshots(bucket_name=bucket_name, s3_client=s3_client, keep=3, verify=args.verify)
            delete_tarfile(tar_filename=tar_filename, verify=args.verify)
        else:
            print("Upload failed.")

    elif args.action == "restore":
        # List the bucket contents and find the latest file
        objects = list_bucket_objects(bucket_name, s3_client)
        if not objects:
            print("No backups available to restore.")
            sys.exit(1)
            
        rename_folder_with_snapshot(folder_path + f"/{folder_name}")

        latest_snapshot = max(objects, key=lambda obj: obj['LastModified'])['Key']

        # Verify before downloading
        if args.verify:
            print(f"Ready to restore {latest_snapshot}. Continue? [y/n]: ", end='')
            if input().lower() != 'y':
                print("Aborting operation.")
                sys.exit(1)
        else:
            print(f"Ready to restore {latest_snapshot}.")

        # Download and extract the file
        if download_file_from_s3(bucket_name, latest_snapshot, latest_snapshot, s3_client):
            extract_tarfile(latest_snapshot, folder_path)
            print("Restore successful.")
            delete_tarfile(latest_snapshot, args.verify)
        else:
            print("Restore failed.")


