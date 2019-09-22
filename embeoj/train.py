"""Functions to create files required for training and generating graph embeddings using PBG
"""
from torchbiggraph.config import parse_config
from torchbiggraph.converters.import_from_tsv import convert_input_data
from torchbiggraph.train import train
from embeoj.utils import load_config, logging
import json
from pathlib import Path, os

GLOBAL_CONFIG = load_config("GLOBAL_CONFIG")
FILENAMES = {
    'train': os.path.join(GLOBAL_CONFIG["DATA_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"],GLOBAL_CONFIG["TSV_FILE_NAME"]+".tsv")
}


def convert_tsv_to_pbg():
    """Reads the tsv file for the graph data and related files are created for training graph embeddings.
    """
    try:
        logging.info("-------------------------CREATING FILES FROM TSV FOR TRAINING------------------------")
        pbg_config_path = os.path.join(GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"],GLOBAL_CONFIG["PBG_CONFIG_NAME"])
        with open(pbg_config_path) as f:
            pbg_config = f.read()
        f.close()
        pbg_config = json.loads(pbg_config)
        pbg_config = parse_config(pbg_config)
        edge_paths = [Path(name) for name in FILENAMES.values()]
        convert_input_data(pbg_config.entities, pbg_config.relations, pbg_config.entity_path, edge_paths, lhs_col=0, rhs_col=2, rel_col=1)
    except Exception as e:
        logging.info("Could not convert to pbg format")
        logging.info(e, exc_info=True)


def train_embeddings(pbg_config):
    """ Carry out training for generating embeddings
    Arguments:
        pbg_config {[type]} -- [description]
    """
    try:
        logging.info("-------------------------TRAINING------------------------")
        train(pbg_config)
    except Exception as e:
        logging.info("error in training")
        logging.info(e, exc_info=True)
