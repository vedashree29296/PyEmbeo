"""Functions to export graph database to json format and create config file for PBG training
"""

from embeoj.utils import connect_to_graphdb, load_config, logging
from pathlib import os
import json

graph_connection = connect_to_graphdb()
GLOBAL_CONFIG = load_config("GLOBAL_CONFIG")


def create_folders():
    """creates folders for storing training data and model checkpoints as mentioned in the config.yml file
    """
    try:
        logging.info(f"""CREATING FOLDERS FOR { GLOBAL_CONFIG["PROJECT_NAME"]}...... """)
        data_path = os.path.join(GLOBAL_CONFIG["DATA_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"])
        model_path = os.path.join(GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"])
        os.makedirs(data_path, exist_ok=True)
        os.makedirs(model_path, exist_ok=True)
        logging.info(f"""Done.""")
    except Exception as e:
        logging.info("Could not create project directories")
        logging.info(e, exc_info=True)


def export_graph_to_json():
    """exports the graph database as a jsonl file
    """
    try: 
        write_directory = os.path.join(GLOBAL_CONFIG["DATA_DIRECTORY"],GLOBAL_CONFIG["PROJECT_NAME"])
        export_file_name = GLOBAL_CONFIG["JSON_EXPORT_FILE"]+".json"
        graph_file_path = os.path.abspath(os.path.join(write_directory, export_file_name))
        logging.info(f"""EXPORT GRAPH DATABASE TO {graph_file_path}...... """)
        query = f"""CALL apoc.export.json.all('{graph_file_path}'"""+""",{batchSize:500})"""
        graph_connection.run(query)
        if os.path.exists(graph_file_path):
            logging.info("Done")
        else:
            logging.info("export failed! try again!")
    except Exception as e:
        logging.info("""error in exporting data. 
        Possible problemas may include incorrect url and credentials. 
        Or absence of apoc procedures. 
        Also make sure apoc settings are configured in neo4j.conf""")
        logging.info(e, exc_info=True)


def export_meta_data():
    """extracts unique entity labels and relationships between them 
    This is then saved in the PBG config
    Note: By  default, PBG accepts only one label per node. 
    Hence the first label is picked by default. 
    (Will come up with an alternate soon!)

    Returns:
        [dict] -- [a basic dictionary specifying the types of entities and labels according to PBG format]
    """
    try:
        logging.info(f"""READING GRAPH METADATA...... """)
        query = """MATCH (n)-[r]->(x) 
        WITH DISTINCT {l1: labels(n), r: type(r), l2: labels(x)} AS connect 
        RETURN head(connect.l1) as lhs,connect.r as name,head(connect.l2) as rhs"""
        metadata = graph_connection.run(query).to_data_frame()
        relations = list(metadata.to_dict("index").values())    
        entities = list(set(list(metadata["lhs"].unique()) + list(metadata["rhs"].unique())))
        config = {"entities": {entity: {"num_partitions": 1,"featurized": False} for entity in entities}, "relations": relations}
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
        logging.info(f"""CREATING CONFIGURATION FILE ...... """)

        default_config = load_config("OPTIONAL_PBG_SETTINGS")
        pbg_config = export_meta_data()
        pbg_config["num_epochs"] = GLOBAL_CONFIG["EPOCHS"]
        pbg_config["dimension"] = GLOBAL_CONFIG["EMBEDDING_DIMENSIONS"]
        pbg_config["entity_path"] = os.path.join(GLOBAL_CONFIG["DATA_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"])
        # change if num of partitions > 1
        pbg_config["edge_paths"] = [os.path.join(GLOBAL_CONFIG["DATA_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"],GLOBAL_CONFIG["TSV_FILE_NAME"]+"_partitioned")]
        pbg_config["checkpoint_path"] = os.path.join(GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"])
        operator = default_config["operator"]
        for relation in pbg_config["relations"]:
            relation["operator"] = operator
        pbg_config = {**pbg_config, **default_config}
        del pbg_config["operator"]
        return pbg_config
    except Exception as e:
        logging.info("Could not create pbg config")
        logging.info(e, exc_info=True)


def save_pbg_config():
    """Saves the PBG config to the checkpoint directory
    """
    try:
        logging.info(f"""SAVING CONFIGURATION FILE ...... """)
        pbg_config = build_pbg_config()
        model_path = os.path.join(GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["PBG_CONFIG_NAME"])
        with open(model_path, "w") as f:
            json.dump(pbg_config, f)
        f.close()
        logging.info(f"""CONFIGURATION FILE SAVED TO {model_path}...... """)
    except Exception as e:
        logging.info("error in saving pbg config")
        logging.info(e, exc_info=True)


def export():
    """entry function for exporting graph data and creating PBG config.
    """
    try:
        logging.info("-------------------------PREPARING FOR DATA EXPORT------------------------")
        create_folders()
        export_graph_to_json()
        save_pbg_config()
        logging.info("Done....")
    except Exception as e:
        logging.info("error in export")
        logging.info(e, exc_info=True)
