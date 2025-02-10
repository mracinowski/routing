from google.cloud import storage

bucketName = "irio-bucket-2025"
storage_client = storage.Client.from_service_account_json("keys.json")


def check_lock(path, last_lock):
    """Checks if the lock (state of file) has changed."""
    return read_file(path) == last_lock


def download_blob_into_memory(bucket_name, blob_name):
    """Downloads a blob into memory."""
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


def upload_blob_from_memory(bucket_name, contents, destination_blob_name):
    """Uploads a file to the bucket."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(contents)

    print(
        f"{destination_blob_name} with contents {contents} uploaded to {bucket_name}."
    )

    
def read_file(path):
    """Reads a file from GCS."""
    return download_blob_into_memory(bucketName, path)


def save_file(path, data: str):
    """Saves a file to GCS."""
    upload_blob_from_memory(bucketName, str(data).encode(), path)
