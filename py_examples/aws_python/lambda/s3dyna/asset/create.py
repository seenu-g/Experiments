import uuid
import http.client as httplib
from asset.asset_model import AssetModel
from log_cfg import logger


def create(event, context):
    """
     No body needed here as POST is a request for a pre-signed upload URL.
     Create an entry for it in dynamo and return upload URL
    """
    logger.debug('event: {}'.format(event))
    asset = AssetModel()
    asset.asset_id = uuid.uuid1().__str__()
    asset.save()
    upload_url = asset.get_upload_url()  # No timeout specified here, use member param default

    return {
        "statusCode": httplib.CREATED,
        "body": {
            'upload_url': upload_url,
            'id': asset.asset_id
        }
    }