import json
import pandas as pd
from embeoj.utils import load_config
from pathlib import os

GLOBAL_CONFIG = load_config("GLOBAL_CONFIG")
json_path = os.path.join(GLOBAL_CONFIG["DATA_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["JSON_EXPORT_FILE"]+".json")


def read_json_file():
    """read exported json(l) file consisting of the graph database
    
    Arguments:
        path {[string]} -- path to the json file
    
    Returns:
        [list] -- list of dictionaries for each node and relation
    """
    try:
        with open(json_path, "r") as json_file:
            json_list = list(json_file)
            json_list = [json.loads(json_string) for json_string in json_list]
        return json_list
    except Exception as e:
        print("error in reading json path")
        print(e)


def separate_nodes_relations(json_list):
    try:
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
        print("error in separating nodes and relations tsv")
        print(e)


def convert_to_tsv(relation_df):
    try:
        tsv_path = os.path.join(GLOBAL_CONFIG["DATA_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["TSV_FILE_NAME"]+".tsv")
        relation_df[["start", "label", "end"]].to_csv(
            tsv_path, sep="\t", header=False, index=False)
    except Exception as e:
        print("error in converting to tsv")
        print(e)


# entry function
def preprocess_exported_data():
    """[summary]
    Arguments:
        path {str} -- [description]
        write_path {str} -- [description]
    """
    try:
        json_list = read_json_file()
        nodes_df, relations_df = separate_nodes_relations(json_list)
        convert_to_tsv(relations_df)
    except Exception as e:
        print("error in preprocessing")
        print(e)
