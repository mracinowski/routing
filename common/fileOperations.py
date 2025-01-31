from google.cloud import storage
import tempfile


bucketName = "irio-bucket-2025"
storage_client = storage.Client.from_service_account_json("keys.json")

# Checks if the lock has changed
def checkLock(path, lastLock):
    return readFile(path) == lastLock

def download_blob_into_memory(bucket_name, blob_name):
    """Downloads a blob into memory."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # blob_name = "storage-object-name"

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(blob_name)
    contents = blob.download_as_bytes()

    print(
        "Downloaded storage object {} from bucket {} as the following bytes object: {}.".format(
            blob_name, bucket_name, contents.decode("utf-8")
        )
    )
    
    return contents.decode("utf-8")



def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Optional: set a generation-match precondition to avoid potential race conditions
    # and data corruptions. The request to upload is aborted if the object's
    # generation number does not match your precondition. For a destination
    # object that does not yet exist, set the if_generation_match precondition to 0.
    # If the destination object already exists in your bucket, set instead a
    # generation-match precondition using its generation number.
    generation_match_precondition = 0

    blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)

    print(
        f"File {source_file_name} uploaded to {destination_blob_name}."
    )
    
def readFile(path):
    return download_blob_into_memory(bucketName, path)

def saveFile(path, data):
    with tempfile.NamedTemporaryFile(delete_on_close=False) as fp:
        fp.write(data)
        upload_blob(bucketName, fp.name, path)
