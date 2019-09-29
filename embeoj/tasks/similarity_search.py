import json
from pathlib import os
from embeoj.utils import logging, connect_to_graphdb
from embeoj.tasks.index import create_indexes, search_all
import sys
import re


graph_connection = connect_to_graphdb()
DATA_DIRECTORY = None
CHECKPOINT_DIRECTORY = None
GLOBAL_CONFIG = None


def find_node(entity_id):
    """ Queries the graph to find the node having a particular id.
      If the the id is not found, then a brute force query is sent to find the node 
      where some property matches with the node id
    
    Arguments:
        entity_id {[str]} -- id of the node to be searched
    
    Returns:
        [dict] -- node with the given id that is found
    """

    try:
        if not re.findall("[a-zA-Z]", entity_id):
            query = f""" MATCH (n) where id(n)= {entity_id} or id(n)= '{entity_id}' 
            return head(labels(n)) as entity_type,n as node, id(n) as entity_id limit 1"""
            entity = graph_connection.run(query).to_data_frame()
            if not entity.empty:
                entity = entity.iloc[0].to_dict()
                entity["node"] = dict(entity["node"])
                return entity
        brute_query = f""" match (n)
        with n, [x in keys(n) WHERE n[x]="{entity_id}"] AS doesMatch
        where size(doesMatch) > 0
        return id(n) as id,head(labels(n)) as entity_type,
        id(n) as entity_id, n as node limit 1"""
        entity = graph_connection.run(brute_query).to_data_frame().dropna()
        if not entity.empty:
            entity = entity.iloc[0].to_dict()
            entity["node"] = dict(entity["node"])
            logging.info(f"ENTITY FOUND : {entity}")
            return entity
        logging.error(f"Could not find node")
    except Exception as e:
        logging.error(f"Node does not exists : {e}", exc_info=True)
        sys.exit(e)


def find_entity_data(entity_id):
    """ Reads the entity_dictionary.json containing ids of all nodes  to locate the index of the entity
    
    Arguments:
        entity_id {[str]} -- id of the node to be searched
    
    Returns:
        [dict] -- dict specifying partition number index of the entity and the file
    """

    try:
        entity = find_node(entity_id)
        logging.info(f"ENTITY FOUND : {entity}")
        entity_type = entity["entity_type"]
        entity_id = str(entity["entity_id"])
        with open(os.path.join(DATA_DIRECTORY, "entity_dictionary.json"), "r") as f:
            all_entity_dictionary = json.load(f)
        f.close()
        entity_dictionaries = [
            ent
            for ent in all_entity_dictionary["all_entities"]
            if ent["entity_type"] == entity_type
        ]  # get all the dictionaries where the entity label is found
        entity_dictionary = [
            entity_dict
            for entity_dict in entity_dictionaries
            if entity_id in entity_dict["entity_ids"]
        ][0]
        entity_index = entity_dictionary["entity_ids"].index(entity_id)
        partition_number = int(entity_dictionary["partition_number"])
        entity_file = entity_dictionary["entity_file"]
        return dict(
            entity_index=entity_index,
            partition_number=partition_number,
            entity_file=entity_file,
            entity_type=entity_type,
        )
    except Exception as e:
        logging.error(f"Could not locate data for node : {e}", exc_info=True)
        sys.exit(e)


def map_back_to_entities(entity_file_list, search_result, neighbors):
    count = 1
    all_similar_ents = list()
    for result in search_result:
        entity_file_list_index = int(result[-1] / neighbors)
        similar_entity_index = int(result[0])
        similar_entity_distance = result[1]
        if similar_entity_distance == 0:
            continue
        entity_filename = (
            f"entity_names_{entity_file_list[entity_file_list_index]}.json"
        )
        entity_filepath = os.path.join(DATA_DIRECTORY, entity_filename)
        node_list = json.load(open(entity_filepath, "r"))
        similar_entity_id = node_list[similar_entity_index]
        similar_entity = find_node(similar_entity_id)
        similar_entity["distance"] = similar_entity_distance
        count += 1
        all_similar_ents.append(similar_entity)
        if count == neighbors:
            break
    return all_similar_ents


def similarity_search(entity_id):
    try:
        from embeoj.utils import load_config

        global GLOBAL_CONFIG, DATA_DIRECTORY, CHECKPOINT_DIRECTORY
        GLOBAL_CONFIG = load_config("GLOBAL_CONFIG")
        DATA_DIRECTORY = os.path.join(
            os.getcwd(), GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["DATA_DIRECTORY"]
        )
        CHECKPOINT_DIRECTORY = os.path.join(
            os.getcwd(),
            GLOBAL_CONFIG["PROJECT_NAME"],
            GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"],
        )

        create_indexes()  # create indexes if not present
        entity_details = find_entity_data(entity_id)
        entity_type = entity_details["entity_type"]
        partition_number = entity_details["partition_number"]
        # find index of entity id
        query_index = entity_details["entity_index"]
        search_result, entity_file_list, neighbors = search_all(
            entity_type, partition_number, query_index
        )
        all_similar_ents = map_back_to_entities(
            entity_file_list, search_result, neighbors
        )
        logging.info("-----------SIMILAR NODES FOUND----------------")
        for s in all_similar_ents:
            logging.info(s)
            logging.info("------------------------")

    except Exception as e:
        logging.error(f"Error in search : {e}", exc_info=True)
        sys.exit(e)
