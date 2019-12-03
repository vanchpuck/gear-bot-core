import unittest
from elasticsearch import Elasticsearch
from gear_bot_core import gear
from time import sleep
import boto3
from botocore.exceptions import ClientError

INDEX = "gear"
DOC_TYPE = "gear"
PAGE_TABLE = "QueryPagination"
DB_REGION_NAME = "us-east-2"
DB_ENDPOINT_URL = "http://localhost:8000"
ELASTIC_HOST = "http://localhost:9200"


class TestGearCatalog(unittest.TestCase):

    catalog = gear.GearCatalog(ELASTIC_HOST, INDEX, PAGE_TABLE, DB_REGION_NAME, 2, DB_ENDPOINT_URL)

    @classmethod
    def setUpClass(cls):
        cls.create_pagination_table()
        es = cls.get_es_instance()
        if len(es.indices.get_alias("*")) == 0:
            es.index(index=INDEX, doc_type=DOC_TYPE, id=1, refresh=True,
                     body={"name": "Petzl lynx", "normalizedName": "Petzl lynx", "oldPrice": 300, "price": 200, "currency": "USD", "store": "rei", "url": "http://rei.com/lynx"})
            es.index(index=INDEX, doc_type=DOC_TYPE, id=2, refresh=True,
                     body={"name": "Petzl Meteor", "normalizedName": "Petzl Meteor", "price": 300, "currency": "USD", "store": "rei", "url": "http://rei.com/meteor"})
            es.index(index=INDEX, doc_type=DOC_TYPE, id=3, refresh=True,
                     body={"name": "Petzl D-Lynx", "normalizedName": "Petzl D-Lynx", "price": 250, "currency": "USD", "store": "rei", "url": "http://rei.com/d-lynx"})
            es.index(index=INDEX, doc_type=DOC_TYPE, id=4, refresh=True,
                     body={"name": "Cyborg crampons", "normalizedName": "Cyborg crampons", "price": 290, "currency": "USD", "store": "rei", "url": "http://rei.com/cyborg"})

    @staticmethod
    def get_es_instance():
        es = Elasticsearch(ELASTIC_HOST, verify_certs=False)
        for _ in range(20):
            sleep(1)
            try:
                es.cluster.health(wait_for_status='yellow')
                return es
            except Exception:
                # Assuming that this exception indicates that table already exist
                continue
        else:
            raise RuntimeError("Elasticsearch failed to start.")

    @classmethod
    def create_pagination_table(cls):
        dynamodb = boto3.resource('dynamodb', region_name=DB_REGION_NAME, endpoint_url=DB_ENDPOINT_URL)
        try:
            dynamodb.create_table(
                TableName=PAGE_TABLE,
                KeySchema=[
                    {
                        'AttributeName': 'ChatId',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'ChatId',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            )
        except ClientError:
            pass

    def test_several_pages(self):
        catalog = self.__class__.catalog
        chat_id = "several_pages_chat"
        self.assertEqual(
            catalog.get_products(chat_id, "Petzl lynx"),
            [
                {'currency': 'USD', 'price': 300, 'store': 'rei', 'url': 'http://rei.com/meteor', 'name': 'Petzl Meteor', "normalizedName": 'Petzl Meteor'},
                {'currency': 'USD', 'price': 200, 'url': 'http://rei.com/lynx', 'name': 'Petzl lynx', 'store': 'rei', 'oldPrice': 300, "normalizedName": 'Petzl lynx'}
            ]
        )
        self.assertEqual(
            catalog.get_products(chat_id),
            [{'currency': 'USD', 'price': 250, 'store': 'rei', 'url': 'http://rei.com/d-lynx', 'name': 'Petzl D-Lynx', "normalizedName": 'Petzl D-Lynx'}]
        )
        self.assertEqual(catalog.get_products(chat_id), None)

    def test_nothing_to_show(self):
        catalog = self.__class__.catalog
        chat_id = "nothing_to_show_chat"
        self.assertEqual(catalog.get_products(chat_id, "Grivel Rambo"), None)
        self.assertEqual(catalog.get_products(chat_id), None)

    def test_close(self):
        catalog = self.__class__.catalog
        chat_id = "close_in_the_middle_chat"
        catalog.get_products(chat_id, "Petzl lynx")
        catalog.close(chat_id)
        self.assertEqual(catalog.get_products(chat_id), None)

    def test_continue_nothing(self):
        catalog = self.__class__.catalog
        chat_id = "continue_nothing_chat"
        self.assertEqual(catalog.get_products(chat_id), None)


if __name__ == '__main__':
    unittest.main()