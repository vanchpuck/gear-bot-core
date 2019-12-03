import json
import boto3
import decimal
import logging


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


class PaginationDB:
    def __init__(self, table_name, region_name, endpoint_url=None):
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name, endpoint_url=endpoint_url)
        self.table = self.dynamodb.Table(table_name)

    def drop_current_position(self, chat_id):
        logging.info("Drop current position. ChatId: {}.".format(chat_id))
        self.table.delete_item(
            Key={
                'ChatId': chat_id
            }
        )

    def set_current_position(self, chat_id, query_str, curr_position):
        logging.info("Set current position. ChatId: {}. QueryString: {}. CurrentPosition: {}.".format(chat_id, query_str, curr_position))
        self.table.put_item(
            Item={
                'ChatId': chat_id,
                'QueryString': query_str,
                'CurrentPosition': curr_position
            }
        )

    def get_current_position(self, chat_id):
        logging.info("Get current position. ChatId: {}.".format(chat_id))
        response = self.table.get_item(
            Key={
                'ChatId': chat_id
            }
        )
        return response['Item'] if 'Item' in response else None
