"""Functions to export graph database to json format and create config file for PBG training
"""

from embeoj.utils import connect_to_graphdb, logging
from pathlib import os
import json
import sys

graph_connection = connect_to_graphdb()
GLOBAL_CONFIG = None
DATA_DIRECTORY = None
CHECKPOINT_DIRECTORY = None


def initialise_config():
    from embeoj.utils import load_config

    global GLOBAL_CONFIG
    global DATA_DIRECTORY
    global CHECKPOINT_DIRECTORY
    GLOBAL_CONFIG = load_config("GLOBAL_CONFIG")
    cwd = os.getcwd()  # get current directory
    # default myproject/data
    DATA_DIRECTORY = os.path.join(
        cwd, GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["DATA_DIRECTORY"]
    )
    # default myproject/model
    CHECKPOINT_DIRECTORY = os.path.join(
        cwd, GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"]
    )


def create_folders():
    """creates folders for storing training data and model checkpoints as per the config.yml file
    """
    try:
        logging.info(
            f"""CREATING FOLDERS FOR { GLOBAL_CONFIG["PROJECT_NAME"]}...... """
        )
        os.makedirs(DATA_DIRECTORY, exist_ok=True)
        os.makedirs(CHECKPOINT_DIRECTORY, exist_ok=True)
        logging.info(f"""Done.""")
    except Exception as e:
        logging.info("Could not create project directories")
        logging.info(e, exc_info=True)
        sys.exit(e)


def export_graph_to_json():
    """exports the graph database as a json file
    """
    try:
        export_file_name = GLOBAL_CONFIG["JSON_EXPORT_FILE"] + ".json"
        graph_file_path = os.path.abspath(
            os.path.join(
                DATA_DIRECTORY, export_file_name
            )  # default:  myproject/data/graph.json
        )
        logging.info(f"""EXPORTING GRAPH DATABASE TO {graph_file_path}...... """)
        query = (
            f"""CALL apoc.export.json.all('{graph_file_path}'"""
            + """,{batchSize:500})"""
        )
        graph_connection.run(query)
        if os.path.exists(graph_file_path):
            logging.info("Done...")
        else:
            logging.info("export failed! try again!")
    except Exception as e:
        logging.info(
            """error in exporting data. 
        Possible problemas may include incorrect url and credentials. 
        Or absence of apoc procedures. 
        Also make sure apoc settings are configured in neo4j.conf"""
        )
        logging.info(e, exc_info=True)
        sys.exit(e)


def save_metafile_details(entities):
    """Save details like num of embedding files, number of entity files etc.
    If partitions are > 1: then there will be 2 entity_name_<label>.json files"""

    try:
        partitions = list(
            range(GLOBAL_CONFIG["NUM_PARTITIONS"])
        )  # number of data partitions default = 1
        versions = list(range(int(GLOBAL_CONFIG["EPOCHS"])))  # final embedding version
        entity_filenames = [
            f"entity_names_{e}_{p}.json" for e in entities for p in partitions
        ]  # entity filenames stored are in format : entity_names_entityname_0.json for number of partitions
        embedding_filenames = [
            f"embeddings_{e}_{p}.v{version}.json"
            for e in entities
            for p in partitions
            for version in versions
        ]  # embedding filenames stored are in format : embeddings_0_0.json for number of partitions
        edge_filenames = [
            f"graph_partitioned/edges{p}_{p1}.h5"
            for p in partitions
            for p1 in partitions
        ]  # edge files are stored are in format : edges_0_0.json for number of partitions
        meta_dict = dict(
            entities=entities,
            partitions=GLOBAL_CONFIG["NUM_PARTITIONS"],
            entity_files=entity_filenames,
            embedding_files=embedding_filenames,
            edge_files=edge_filenames,
        )  # metadata for all these files
        metadata_path = os.path.join(
            os.getcwd(), GLOBAL_CONFIG["PROJECT_NAME"], "metadata.json"
        )  # save to myproject/metadata.json
        with open(metadata_path, "w") as f:
            json.dump(meta_dict, f)
        f.close()
    except Exception as e:
        logging.info("""error in exporting meta data. """)
        logging.info(e, exc_info=True)


def export_meta_data():
    """extracts unique entity labels and relationships between them 
    This is then saved in the PBG config
    Note: By  default, PBG accepts only one label per node. 
    Hence the first label is picked by default. 

    Returns:
        [dict] -- [a basic dictionary specifying the types of entities and labels according to PBG format]
    """
    try:
        logging.info(f"""READING GRAPH METADATA...... """)
        query = """MATCH (n)-[r]->(x) 
        WITH DISTINCT {l1: labels(n), r: type(r), l2: labels(x)} AS connect 
        RETURN head(connect.l1) as lhs,connect.r as name,head(connect.l2) as rhs"""
        metadata = graph_connection.run(query).to_data_frame()
        relations = list(metadata.to_dict("index").values())  # all relations
        entities = list(
            set(list(metadata["lhs"].unique()) + list(metadata["rhs"].unique()))
        )  # unique names of entities
        partitions = GLOBAL_CONFIG["NUM_PARTITIONS"]
        config = {
            "entities": {
                entity: {"num_partitions": partitions, "featurized": False}
                for entity in entities
            },
            "relations": relations,
        }
        save_metafile_details(entities)
        return config
    except Exception as e:
        logging.info("Could not export graph metadata")
        logging.info(e, exc_info=True)


def build_pbg_config():
    """Creates the PBG config 

    Returns:
        [dict] -- [config in PBG format]
    """
    try:
        from embeoj.utils import load_config

        logging.info(f"""CREATING CONFIGURATION FILE FOR TRAINING...... """)
        default_config = load_config("OPTIONAL_PBG_SETTINGS")
        pbg_config = export_meta_data()
        pbg_config["num_epochs"] = GLOBAL_CONFIG["EPOCHS"]
        pbg_config["dimension"] = GLOBAL_CONFIG["EMBEDDING_DIMENSIONS"]
        pbg_config["entity_path"] = DATA_DIRECTORY
        # change if num of partitions > 1
        pbg_config["edge_paths"] = [
            os.path.join(
                DATA_DIRECTORY, GLOBAL_CONFIG["TSV_FILE_NAME"] + "_partitioned"
            )
        ]
        pbg_config["checkpoint_path"] = CHECKPOINT_DIRECTORY
        operator = default_config["operator"]
        for relation in pbg_config["relations"]:
            relation["operator"] = operator  # adds operator for each relation
        pbg_config = {
            **pbg_config,
            **default_config,
        }  # merge the default and added config
        del pbg_config["operator"]  # removes extra key from config to avoid error
        return pbg_config
    except Exception as e:
        logging.info("Could not create pbg config")
        logging.info(e, exc_info=True)


def save_pbg_config():
    """Saves the PBG config to the checkpoint directory
    """
    try:
        pbg_config = build_pbg_config()
        model_path = os.path.join(
            CHECKPOINT_DIRECTORY, GLOBAL_CONFIG["PBG_CONFIG_NAME"]
        )
        with open(model_path, "w") as f:
            json.dump(pbg_config, f)
        f.close()
        logging.info(f"""CONFIGURATION FILE SAVED TO {model_path}...... """)
    except Exception as e:
        logging.info("error in saving pbg config")
        logging.info(e, exc_info=True)
        sys.exit(e)


def export():
    """entry function for exporting graph data and creating PBG config.
    """
    try:
        initialise_config()
        logging.info(
            "-------------------------PREPARING FOR DATA EXPORT------------------------"
        )
        create_folders()  # create neccesary folders
        export_graph_to_json()  # export graph to json
        save_pbg_config()  # create and save config.json for training
        logging.info("Done....")
    except Exception as e:
        logging.info("error in export")
        logging.info(e, exc_info=True)
        sys.exit(e)
