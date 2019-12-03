from elasticsearch import Elasticsearch
from . import pagination
import logging


class GearCatalog:

    def __init__(self, es_host, index_name, db_table_name, db_region_name, page_size, db_endpoint_url=None):
        self.es = Elasticsearch([es_host], verify_certs=False)
        self.page_db = pagination.PaginationDB(db_table_name, db_region_name, db_endpoint_url)
        self.page_size = page_size
        self.index_name = index_name

    def get_products(self, chat_id, request_str=None):
        gear_data = self.__get_next_page(chat_id) if request_str is None \
            else self.__get_first_page(chat_id, request_str)
        logging.info("Products data: {}".format(gear_data))

        return None if gear_data is None or len(gear_data) == 0 \
            else list(map(lambda hit: hit["_source"], gear_data['hits']['hits']))

    def close(self, chat_id):
        self.page_db.drop_current_position(chat_id)

    def __get_page(self, chat_id, query_str, start_from):
        logging.info("Getting the page. chat_id = {}, query_string = {}, page_size = {}".format(chat_id, query_str, self.page_size))
        result = self.__es_query(query_str, start_from)
        total_hits = result['hits']['total']
        next_position = self.page_size + start_from
        if next_position >= total_hits:
            logging.info("No more products matched. Dropping the page index.")
            self.page_db.drop_current_position(chat_id)
        else:
            logging.info("Updating the page index. page_index = {}".format(next_position))
            self.page_db.set_current_position(chat_id, query_str, next_position)
        return result if total_hits > 0 else None

    def __get_first_page(self, chat_id, query_str):
        logging.info("Getting the first page. chat_id = {}, query_str = {}".format(chat_id, query_str))
        return self.__get_page(chat_id, query_str, 0)

    def __get_next_page(self, chat_id):
        logging.info("Getting next page for chat_id = {}".format(chat_id))
        query_from = self.page_db.get_current_position(chat_id)
        if query_from is not None:
            query_str = query_from['QueryString']
            logging.info("Last query string = {}".format(query_str))
            last_position = query_from['CurrentPosition']
            logging.info("Next page start position = {}".format(last_position))
            return self.__get_page(chat_id, query_str, last_position)
        else:
            logging.info("No pagination info found for chat_id = {}".format(chat_id))
            return None

    def __es_query(self, query_str, start_from):
        logging.info("Query string: {}. From: {}. Size: {}".format(query_str, start_from, self.page_size))
        return self.es.search(
            index=self.index_name,
            body={
                "from": start_from, "size": self.page_size,
                "query": {
                    "match": {
                        "normalizedName": query_str
                    }
                }
            }
        )