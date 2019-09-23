"""
General utility functions
"""
from py2neo import Graph
import yaml
from yaml.loader import Loader
import logging


CONFIG_FILE_PATH = "config.yml"

logging.basicConfig(format="%(asctime)s - %(message)s", level=0)
logging.info("Logging enabled at INFO")


def load_config(subconfig_name: str = None):
    """Loads config in YAML file. Can load one part of the config or 
    the entire config if subconfig_name is not given
    subconfig_name can be from: [GLOBAL_CONFIG, GRAPH_DATABASE, OPTIONAL_PBG_SETTINGS]
    
    Keyword Arguments:
        subconfig_name {str} -- part of the config to load (default: {None})
    
    Returns:
        [dict] -- [config file]
    """
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
    """connect to graph database
    Returns:
        [type] -- [connection to graph database]
    """
    try:
        graph_config = load_config("GRAPH_DATABASE")
        url = graph_config["NEO4J_URL"]
        username = graph_config["NEO4J_USER"]
        password = graph_config["NEO4J_PASSWORD"]
        graph_db = Graph(url,
                         user=username,
                         password=password)
        return graph_db
    except Exception as e:
        print(f"Error in connecting to graph database : {e}")
