"""Functions to create files required for training and generating graph embeddings using PBG
"""
from torchbiggraph.config import parse_config
from torchbiggraph.converters.import_from_tsv import convert_input_data
from torchbiggraph.train import train
import json
from pathlib import Path, os
import sys
import logging


logger = logging.getLogger("torchbiggraph")  # log to stout
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
# handler.setFormatter(CustomLoggingFormatter())
logging.basicConfig(handlers=[handler])


GLOBAL_CONFIG = None
DATA_DIRECTORY = None
CHECKPOINT_DIRECTORY = None
FILENAMES = None


def initialise_config():
    from embeoj.utils import load_config

    global GLOBAL_CONFIG
    global DATA_DIRECTORY
    global CHECKPOINT_DIRECTORY
    global FILENAMES
    GLOBAL_CONFIG = load_config("GLOBAL_CONFIG")

    FILENAMES = {
        "train": os.path.join(
            os.getcwd(),
            GLOBAL_CONFIG["PROJECT_NAME"],
            GLOBAL_CONFIG["DATA_DIRECTORY"],
            GLOBAL_CONFIG["TSV_FILE_NAME"] + ".tsv",
        )
    }  # path to tsv file with train data
    DATA_DIRECTORY = os.path.join(
        os.getcwd(), GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["DATA_DIRECTORY"]
    )

    CHECKPOINT_DIRECTORY = os.path.join(
        os.getcwd(),
        GLOBAL_CONFIG["PROJECT_NAME"],
        GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"],
    )


def load_pbg_config():
    """ reads config.json file and creates a schema object  for the config
    
    Returns:
        [object] -- Config Schema object for the json file
    """
    try:
        initialise_config()
        logging.info(CHECKPOINT_DIRECTORY)
        pbg_config_path = os.path.join(
            CHECKPOINT_DIRECTORY, GLOBAL_CONFIG["PBG_CONFIG_NAME"]
        )
        with open(pbg_config_path) as f:
            pbg_config = f.read()
        f.close()
        pbg_config = json.loads(pbg_config)
        pbg_config = parse_config(pbg_config)
        return pbg_config
    except Exception as e:
        logging.info("Could not convert to pbg format")
        logging.info(e, exc_info=True)
        sys.exit(e)


def convert_tsv_to_pbg():
    """Reads the tsv file for the graph data and related files are created for training graph embeddings.
    """
    try:
        global FILENAMES
        logging.info(
            "-------------------------CREATING FILES FROM TSV FOR TRAINING------------------------"
        )
        pbg_config = load_pbg_config()
        edge_paths = [Path(name) for name in FILENAMES.values()]
        convert_input_data(
            pbg_config.entities,
            pbg_config.relations,
            pbg_config.entity_path,
            pbg_config.edge_paths,
            edge_paths,
            lhs_col=0,
            rhs_col=2,
            rel_col=1,
        )
    except Exception as e:
        logging.info("Could not convert to pbg format")
        logging.info(e, exc_info=True)
        sys.exit(e)


def merge_entity_name_files():
    """merges all the json files having entity names and their ids to one file called entity_dictionary.json
    this usually takes place in case number of partitions >1.
    This can then be used for other downstream tasks 
    """
    try:
        global DATA_DIRECTORY
        global GLOBAL_CONFIG
        metadata_path = os.path.join(
            os.getcwd(), GLOBAL_CONFIG["PROJECT_NAME"], "metadata.json"
        )  # read metadata
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        f.close()
        all_entities = []
        entity_files = metadata[
            "entity_files"
        ]  # get a list of all json files having entities' ids
        for entity_file in entity_files:
            partition_number = int(os.path.splitext(entity_file)[0].split("_")[-1])
            entity_type = "_".join(
                os.path.splitext(entity_file)[0]
                .replace("entity_names_", "")
                .split("_")[:-1]
            ).strip(
                "_"
            )  # find the entity type
            entity_file_path = os.path.join(DATA_DIRECTORY, entity_file)
            entity_data = json.load(open(entity_file_path, "r"))
            entity_dict = dict(
                entity_ids=entity_data,
                entity_type=entity_type,
                partition_number=partition_number,
                entity_file=entity_file,
            )  # creates a dict object for one partition
            all_entities.append(entity_dict)
        with open(os.path.join(DATA_DIRECTORY, "entity_dictionary.json"), "w") as f:
            json.dump(dict(all_entities=all_entities), f)
        f.close()
    except Exception as e:
        logging.info("Could not create a file for all the entities")
        logging.info(e, exc_info=True)


def train_embeddings():
    """ Train function for generating embeddings
    Arguments:
        pbg_config {[object]} -- [config object]
    """
    try:
        initialise_config()
        pbg_config = load_pbg_config()
        merge_entity_name_files()
        logging.info("-------------------------TRAINING------------------------")
        train(pbg_config)
    except Exception as e:
        logging.info("error in training")
        logging.info(e, exc_info=True)
        sys.exit(e)
