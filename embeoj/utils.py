"""
General utility functions
"""
from py2neo import Graph
import yaml
from yaml.loader import Loader
import logging


CONFIG_FILE_PATH = "./config.yml"
logging.basicConfig(format="%(asctime)s - %(message)s", level=20)


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
        logging.info(f"Error in loading config : {e}", exc_info=True)


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
        graph_db = Graph(url, user=username, password=password)
        return graph_db
    except Exception as e:
        logging.info(f"Error in connecting to graph database : {e}", exc_info=True)


def update_config(**kwargs):
    try:
        logging.info("-----------------UPDATING CONFIG-----------------")
        default_config = load_config()
        for key, value in kwargs.items():
            if default_config["GLOBAL_CONFIG"].get(key.upper()):
                default_config["GLOBAL_CONFIG"][key.upper()] = value
            elif default_config["GRAPH_DATABASE"].get(key.upper()):
                default_config["GRAPH_DATABASE"][key.upper()] = value
            elif default_config.get(key):
                default_config[key] = value
        with open(CONFIG_FILE_PATH, "w") as f:
            yaml.dump(default_config, f)
        logging.info("Done....")
    except Exception as e:
        logging.info(f"Error in updating config : {e}", exc_info=True)
