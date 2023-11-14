import json
import logging

from azure.storage.blob import BlobServiceClient
from util import cache_results


logging = logging.getLogger(__name__)

## @classname BlobService
## @brief Class to handle blob storage
class BlobService:
    ## @classmethod __init__
    ## @brief Initialize the BlobServiceClient
    ## @param connection_string: connection string to blob storage
    def __init__(self, connection_string: str) -> None:
        self.blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        self.container_name = "momentum-strategy"
        self.container_client = self.blob_service_client.get_container_client(
            self.container_name
        )
        if self.container_client.exists():
            logging.info("%s container already exists", self.container_name)
        else:
            logging.info("%s container does not exist", self.container_name)
            self.container_client.create_container()

    ## @classmethod get_blob_data_if_exists
    ## @brief Get blob data if exists
    ## @param blob_name: name of the blob
    ## @return blob_data: blob data if exists else None
    @cache_results
    def get_blob_data_if_exists(self, blob_name: str):
        blob_client = self.container_client.get_blob_client(blob_name)
        if blob_client.exists():
            logging.info("%s blob already exists", blob_name)
            return json.loads(blob_client.download_blob().readall())
        logging.info("%s blob does not exist", blob_name)
        return None

    ## @classmethod upload_blob
    ## @brief Upload blob data
    ## @param blob_data: blob data to upload
    ## @param blob_name: name of the blob
    def upload_blob(self, blob_data: dict, blob_name: str):
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_client.upload_blob(json.dumps(blob_data, indent=2), overwrite=True)

    ## @classmethod list_blobs
    ## @brief List all blobs
    ## @return blob_list: list of all blobs
    def list_blobs(self, file_prefix: str = None):
        blob_list = self.container_client.list_blobs(name_starts_with=file_prefix)
        ## just return the blob name
        return [blob.name for blob in blob_list]
