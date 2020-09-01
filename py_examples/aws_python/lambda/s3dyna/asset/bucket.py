import http.client as httplib
import os
from pynamodb.exceptions import DoesNotExist, DeleteError, UpdateError
from asset.asset_model import AssetModel
from log_cfg import logger


def event(event, context):
    """
    Triggered by s3 events, object create and remove
    """
    logger.debug('event: {}'.format(event))
    event_name = event['Records'][0]['eventName']
    key = event['Records'][0]['s3']['object']['key']
    asset_id = key.replace('{}/'.format(os.environ['S3_KEY_BASE']), '')

    try:
        if 'ObjectCreated:Put' == event_name:

            try:
                asset = AssetModel.get(hash_key=asset_id)
                asset.mark_received()
            except UpdateError:
                return {
                    'statusCode': httplib.BAD_REQUEST,
                    'body': {
                        'error_message': 'Unable to update ASSET'}
                }

        elif 'ObjectRemoved:Delete' == event_name:

            try:
                asset = AssetModel.get(hash_key=asset_id)
                asset.delete()
            except DeleteError:
                return {
                    'statusCode': httplib.BAD_REQUEST,
                    'body': {
                        'error_message': 'Unable to delete ASSET {}'.format(asset)
                    }
                }

    except DoesNotExist:
        return {
            'statusCode': httplib.NOT_FOUND,
            'body': {
                'error_message': 'ASSET {} not found'.format(asset_id)
            }
        }

    return {'statusCode': httplib.ACCEPTED}