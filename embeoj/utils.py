"""
General utility functions
"""
from py2neo import Graph
import yaml
from yaml.loader import Loader

CONFIG_FILE_PATH = "config.yml"


def load_config(subconfig_name: str = None):
    try:
        config_file = open(CONFIG_FILE_PATH).read()
        config = yaml.load(config_file, Loader=Loader)
        if subconfig_name is not None:
            subconfig = config[subconfig_name]
            return subconfig
        return config
    except Exception as e:
        print(f"Error in loading config file : {e}")


def connect_to_graphdb():
    try:
        graph_config = load_config("graph_database_config")
        url = graph_config["NEO4J_URL"]
        username = graph_config["NEO4J_USER"]
        password = graph_config["NEO4J_PASSWORD"]
        graph_db = Graph(url,
                         user=username,
                         password=password)
        return graph_db
    except Exception as e:
        print(f"Error in connecting to graph database : {e}")