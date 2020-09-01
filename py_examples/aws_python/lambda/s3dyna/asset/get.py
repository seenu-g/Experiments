import os
import http.client as httplib
from pynamodb.exceptions import DoesNotExist
from asset.asset_model import AssetModel
from log_cfg import logger


def get(event, context):
    """
    Get a presigned download URL for asset <asset-id>
    """
    logger.debug('event: {}'.format(event))
    try:
        ttl = os.environ['URL_DEFAULT_TTL']
        try:
            ttl = int(event['query']['timeout'])
        except KeyError or ValueError:
            pass
        asset_id = event['path']['asset_id']
        asset = AssetModel.get(hash_key=asset_id)
        download_url = asset.get_download_url(ttl)

    except DoesNotExist:
        return {
            'statusCode': httplib.NOT_FOUND,
            'body': {
                'error_message': 'ASSET {} not found'.format(asset_id)
            }
        }

    except AssertionError as e:
        return {
            'statusCode': httplib.FORBIDDEN,
            'body': {
                'error_message': 'Unable to download: {}'.format(e)
            }
        }

    return {
        "statusCode": httplib.ACCEPTED,
        "body": {
            'download_url': download_url
        }
    }