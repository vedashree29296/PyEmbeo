"""Converts graph database exported in jsonl format to tsv format required by PBG
"""
import json
import pandas as pd
from embeoj.utils import load_config, logging
from pathlib import os

GLOBAL_CONFIG = load_config("GLOBAL_CONFIG")
json_path = os.path.join(GLOBAL_CONFIG["DATA_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["JSON_EXPORT_FILE"]+".json")


def read_json_file():
    """read exported json(l) file consisting of the graph database
    Returns:
        [list] -- list of dictionaries for each node and relation
    """
    try:
        logging.info(f"READING GRAPH DATA IN JSON FROM {json_path}")
        with open(json_path, "r") as json_file:
            json_list = list(json_file)
            json_list = [json.loads(json_string) for json_string in json_list]
        return json_list
    except Exception as e:
        logging.info("error in reading json path")
        logging.info(e, exc_info=True)


def separate_nodes_relations(json_list):
    """Creates two separate dataframes for the nodes and the relationships
    
    Arguments:
        json_list {[list]} -- list of node/relationship dictionaries
    
    Returns:
        [Dataframe] -- dataframes for the nodes and the relationships
    """
    try:
        logging.info(f"SEPARATING NODES AND RELATIONSHIPS")

        graph_df = pd.DataFrame(json_list)
        nodes_df = graph_df[graph_df["type"] == "node"][
            ["id", "type", "labels", "properties"]
        ]
        relation_df = graph_df[graph_df["type"] == "relationship"][
            ["type", "start", "end", "label", "properties"]
        ]
        nodes_df["labels"] = nodes_df["labels"].apply(lambda x: x[0])
        relation_df["start"] = relation_df["start"].apply(lambda x: x["id"])
        relation_df["end"] = relation_df["end"].apply(lambda x: x["id"])
        return nodes_df, relation_df
    except Exception as e:
        logging.info("error in separating nodes and relations tsv")
        logging.info(e, exc_info=True)


def convert_to_tsv(relation_df):
    """Converts the Dataframe to tsv for PBG to read.
    each row is in the triplet format that defines one edge/relationship in the graph
    columns: start,label,end
        - start: id of the 'from' node
        - end: id of the 'to' node
        - label: type of the relationship
    
    Arguments:
        relation_df {[Dataframe]} -- Dataframe in above mentioned format
    """
    try:
        tsv_path = os.path.join(GLOBAL_CONFIG["DATA_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["TSV_FILE_NAME"]+".tsv")
        logging.info(f"WRITING TSV FILE TO {tsv_path}")
        relation_df[["start", "label", "end"]].to_csv(
            tsv_path, sep="\t", header=False, index=False)
    except Exception as e:
        logging.info("error in converting to tsv")
        logging.info(e, exc_info=True)


# entry function
def preprocess_exported_data():
    """entry function for converting graph export data in jsonl format to tsv format supported by PBG
    """
    try:
        logging.info("-------------------------PREPROCESSING DATA------------------------")
        json_list = read_json_file()
        nodes_df, relations_df = separate_nodes_relations(json_list)
        convert_to_tsv(relations_df)
        logging.info("Done")
    except Exception as e:
        logging.info("error in preprocessing")
        logging.info(e, exc_info=True)
