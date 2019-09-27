import faiss
import json
from pathlib import os
import h5py
from embeoj.utils import load_config, logging
import re

# graph_connection = connect_to_graphdb()
SIMILARITY_SEARCH_CONFIG = load_config("SIMILARITY_SEARCH_CONFIG")
GLOBAL_CONFIG = load_config("GLOBAL_CONFIG")
index_path = os.path.join(
    os.getcwd(),
    GLOBAL_CONFIG["PROJECT_NAME"],
    GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"],
    SIMILARITY_SEARCH_CONFIG["INDEX_FILE_NAME"],
)
DATA_DIRECTORY = os.path.join(
    os.getcwd(), GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["DATA_DIRECTORY"]
)
CHECKPOINT_DIRECTORY = os.path.join(
    os.getcwd(), GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"]
)


def create_faiss_index(index_name: str):
    """[summary]
    
    Arguments:
        index_name {str} -- [description]
    
    Returns:
        [type] -- [description]
    """
    try:
        dimensions = GLOBAL_CONFIG["EMBEDDING_DIMENSIONS"]
        nlist = SIMILARITY_SEARCH_CONFIG["NUM_CLUSTER"]
        if index_name == "IndexIVFFlat":
            quantizer = faiss.IndexFlatL2(dimensions)
            index = faiss.IndexIVFFlat(quantizer, dimensions, nlist)
        elif index_name == "IndexFlatL2":
            index = faiss.IndexFlatL2(dimensions)
        return index
    except Exception as e:
        logging.error(f"Could not create index: {e}", exc_info=True)


def get_checkpoint_version():
    """returns the latest version of the embeddings 
    
    Returns:
        [int] -- version of the embeddings
    """
    try:
        checkpoint_version_file = os.path.join(
            GLOBAL_CONFIG["PROJECT_NAME"],
            GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"],
            "checkpoint_version.txt",
        )
        with open(checkpoint_version_file, "r") as f:
            version = f.read()
        f.close()
        version = int(version.split()[0].strip())
        logging.info(f"Latest checkpoint version: {version}")
        return version
    except Exception as e:
        logging.error(f"Could locate checkpoint version file: {e}", exc_info=True)


def read_embeddings(entity_file):
    """[summary]
    
    Arguments:
        entity_file {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """
    try:
        version = get_checkpoint_version()
        entity_type = "_".join(entity_file.split("_")[2:-1]).strip("_")
        partition_no = os.path.splitext(entity_file)[0].split("_")[-1]
        embedding_file = f"embeddings_{entity_type}_{partition_no}.v{version}.h5"
        logging.info(f"embedding file name: {embedding_file}")
        embeddings_path = os.path.join(
            GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"],
            GLOBAL_CONFIG["PROJECT_NAME"],
            embedding_file,
        )
        with h5py.File(embeddings_path, "r") as hf:
            embeddings = hf["embeddings"][...]
        hf.close()
        return embeddings
    except Exception as e:
        logging.info(f"error in reading embedding h5 file: {e}", exc_info=True)


def save_index(entity_file):
    try:
        index_name = SIMILARITY_SEARCH_CONFIG["FAISS_INDEX_NAME"]
        index = create_faiss_index(index_name)
        embeddings = read_embeddings(entity_file)
        if index_name == "IndexIVFFlat":
            index.train(embeddings)
        index.add(embeddings)
        faiss.write_index(index, index_path)
        return index
    except Exception as e:
        logging.info(f"error in index creation: {e}", exc_info=True)


def load_index(entity_file):
    try:
        if os.path.exists(index_path):
            logging.info(f"reading index file: {index_path}")
            index = faiss.read_index(index_path)
            return index
        else:
            save_index(entity_file)
            return index
    except Exception as e:
        logging.error(f"Error in Indexing : {e}", exc_info=True)


def read_metadata_files():
    try:
        data_directory = os.path.join(
            GLOBAL_CONFIG["PROJECT_NAME"],
            GLOBAL_CONFIG["DATA_DIRECTORY"],
            "metadata.json",
        )
        metadata_path = os.path.join(data_directory, "metadata.json")
        metadata = json.load(open(metadata_path, "r"))
        entity_files = metadata["entity_files"]

    except Exception as e:
        logging.error(f"Error in Indexing : {e}", exc_info=True)


def return_entity_index(entity_id):
    try:
        data_directory = os.path.join(
            GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["DATA_DIRECTORY"]
        )
        # read entity files having name as entity_names_<entityname>_<partition_no>.json
        logging.info(data_directory)
        logging.info(os.listdir(data_directory))
        entity_files = [
            re.findall("entity_names_[a-zA-Z]*[_][0-9]{1,2}.json", filename)
            for filename in os.listdir(data_directory)
        ]
        entity_files = [f[0] for f in entity_files if f]
        logging.info(entity_files)
        # read entity names
        for entity_file in entity_files:
            with open(os.path.join(data_directory, entity_file), "rt") as tf:
                entity_names = json.load(tf)
                query_entity_index = entity_names.index(entity_id)
            tf.close()
            # entity found
            if query_entity_index is not None:
                # a dumb way to get the type find a better way
                logging.info(
                    f"entity found in {entity_file} at index {query_entity_index}"
                )
                return entity_file, query_entity_index
        # if a global dictionary exists in case an "all" entity is given
        with open(os.path.join(data_directory, "dictionary.json"), "rt") as tf:
            entity_names = json.load(tf)["entities"]["all"]
            query_entity_index = entity_names.index(entity_id)
        tf.close()
        if query_entity_index is not None:
            return "dictionary.json", query_entity_index
        return None
    except Exception as e:
        logging.error(f"Error in Indexing : {e}", exc_info=True)


def map_back_to_entities(entity_file, indices):
    try:
        data_directory = os.path.join(
            GLOBAL_CONFIG["DATA_DIRECTORY"], GLOBAL_CONFIG["PROJECT_NAME"]
        )
        with open(os.path.join(data_directory, entity_file), "rt") as tf:
            entity_names = json.load(tf)
        tf.close()
        mapped_entities = [entity_names[index] for index in list(indices[0])]
        return mapped_entities
    except Exception as e:
        logging.error(f"Error in mapping back to entities : {e}", exc_info=True)


def similarity_search(entity_name):
    try:
        dimensions = GLOBAL_CONFIG["EMBEDDING_DIMENSIONS"]  # get number of dimensions
        neighbors = SIMILARITY_SEARCH_CONFIG[
            "NEAREST_NEIGHBORS"
        ]  # get number fo nearest neighbours
        # find index of entity id
        entity_file, query_entity_index = return_entity_index(entity_name)
        # check if entity is not found
        if query_entity_index is None:
            logging.info("Couldn't find the entity you were searching for")
            return
        # get embedding from h5 file for entity
        embeddings = read_embeddings(entity_file)
        query_entity_embedding = embeddings[query_entity_index, :]
        query_entity_embedding = query_entity_embedding.reshape((1, dimensions))
        index = load_index(entity_file)
        # search in faiss
        distances, indices = index.search(query_entity_embedding, neighbors)
        logging.info(indices)
        mapped_entities = map_back_to_entities(entity_file, indices)
        logging.info(f"mapped_entities: {mapped_entities}")
    except Exception as e:
        logging.error(f"Error in Indexing : {e}", exc_info=True)
