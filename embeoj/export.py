from embeoj.utils import connect_to_graphdb, load_config
from pathlib import os
import json

graph_connection = connect_to_graphdb()
GLOBAL_CONFIG = load_config("GLOBAL_CONFIG")


def create_folders():
    try:
        data_path = os.path.join(GLOBAL_CONFIG["DATA_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"])
        model_path = os.path.join(GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"])
        os.makedirs(data_path, exist_ok=True)
        os.makedirs(model_path, exist_ok=True)
    except Exception as e:
        print("Could not create project directories")
        print(e)


def export_graph_to_json():
    try:
        write_directory = os.path.join(GLOBAL_CONFIG["DATA_DIRECTORY"],GLOBAL_CONFIG["PROJECT_NAME"])
        export_file_name = GLOBAL_CONFIG["JSON_EXPORT_FILE"]+".json"
        graph_file_path = os.path.abspath(os.path.join(write_directory, export_file_name))
        query = f"""CALL apoc.export.json.all('{graph_file_path}'"""+""",{batchSize:500})"""
        graph_connection.run(query)
        if os.path.exists(graph_file_path):
            print("exported graph data")
        else:
            print("export failed! try again!")
    except Exception as e:
        print("""error in exporting data. 
        Possible problemas may include incorrect url and credentials. 
        Or absence of apoc procedures. 
        Also make sure apoc settings are configured in neo4j.conf""")
        print(e)


def export_meta_data():
    try:
        query = """MATCH (n)-[r]->(x) 
        WITH DISTINCT {l1: labels(n), r: type(r), l2: labels(x)} AS connect 
        RETURN head(connect.l1) as lhs,connect.r as name,head(connect.l2) as rhs"""
        metadata = graph_connection.run(query).to_data_frame()
        relations = list(metadata.to_dict("index").values())    
        entities = list(set(list(metadata["lhs"].unique()) + list(metadata["rhs"].unique())))
        config = {"entities": {entity: {"num_partitions": 1,"featurized": False} for entity in entities}, "relations": relations}
        return config
    except Exception as e:
        print("Could not export graph metadata")
        print(e)


def build_pbg_config():
    try:
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
        print("Could not create pbg config")
        print(e)


def save_pbg_config():
    try:
        pbg_config = build_pbg_config()
        model_path = os.path.join(GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["PBG_CONFIG_NAME"])
        with open(model_path, "w") as f:
            json.dump(pbg_config, f)
        f.close()
    except Exception as e:
        print("error in saving pbg config")
        print(e)


def export():
    try:
        create_folders()
        export_graph_to_json()
        save_pbg_config()
    except Exception as e:
        print("error in export")
        print(e)
