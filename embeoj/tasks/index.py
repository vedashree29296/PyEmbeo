import faiss
import json
from pathlib import os
import h5py
import numpy as np
from embeoj.utils import logging, get_checkpoint_version

# graph_connection = connect_to_graphdb()
SIMILARITY_SEARCH_CONFIG = None
GLOBAL_CONFIG = None
DATA_DIRECTORY = None
CHECKPOINT_DIRECTORY = None
FAISS_INDEX_NAME = None
EMBEDDING_DIMENSIONS = None
NUM_CLUSTER = None
neighbors = None


def initialise_config():
    from embeoj.utils import load_config

    global SIMILARITY_SEARCH_CONFIG
    global GLOBAL_CONFIG
    global DATA_DIRECTORY
    global CHECKPOINT_DIRECTORY
    global FAISS_INDEX_NAME
    global EMBEDDING_DIMENSIONS
    global NUM_CLUSTER
    global neighbors

    SIMILARITY_SEARCH_CONFIG = load_config("SIMILARITY_SEARCH_CONFIG")
    GLOBAL_CONFIG = load_config("GLOBAL_CONFIG")
    DATA_DIRECTORY = os.path.join(
        os.getcwd(), GLOBAL_CONFIG["PROJECT_NAME"], GLOBAL_CONFIG["DATA_DIRECTORY"]
    )
    CHECKPOINT_DIRECTORY = os.path.join(
        os.getcwd(),
        GLOBAL_CONFIG["PROJECT_NAME"],
        GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"],
    )
    FAISS_INDEX_NAME = SIMILARITY_SEARCH_CONFIG["FAISS_INDEX_NAME"]
    EMBEDDING_DIMENSIONS = GLOBAL_CONFIG["EMBEDDING_DIMENSIONS"]
    NUM_CLUSTER = SIMILARITY_SEARCH_CONFIG["NUM_CLUSTER"]
    neighbors = SIMILARITY_SEARCH_CONFIG["NEAREST_NEIGHBORS"] + 1


def create_index_directory():
    try:
        index_directory = os.path.join(CHECKPOINT_DIRECTORY, "index")
        os.makedirs(index_directory, exist_ok=True)
    except Exception as e:
        logging.error(f"Could not create index: {e}", exc_info=True)


def create_faiss_index():
    """Creates the index for the embeddings 

    Arguments:
        index_name {str} -- Name of faiss index to use

    Returns:
        faiss index of given type
    """
    try:

        if FAISS_INDEX_NAME == "IndexIVFFlat":
            quantizer = faiss.IndexFlatL2(EMBEDDING_DIMENSIONS)
            index = faiss.IndexIVFFlat(quantizer, EMBEDDING_DIMENSIONS, NUM_CLUSTER)
        elif FAISS_INDEX_NAME == "IndexFlatL2":
            index = faiss.IndexFlatL2(EMBEDDING_DIMENSIONS)
        return index
    except Exception as e:
        logging.error(f"Could not create index: {e}", exc_info=True)


def read_embeddings(entity_type, partition_number):
    """Reads embeddings (.h5) files

    Arguments:
        entity_type {[str]} -- label of node
        partition_number {[int]} -- partition in which the node lies

    Returns:
        [type] -- [description]
    """
    try:
        version = get_checkpoint_version()
        embedding_file = f"embeddings_{entity_type}_{partition_number}.v{version}.h5"
        logging.info(f"embedding file name: {embedding_file}")
        embeddings_path = os.path.join(
            GLOBAL_CONFIG["PROJECT_NAME"],
            GLOBAL_CONFIG["CHECKPOINT_DIRECTORY"],
            embedding_file,
        )
        with h5py.File(embeddings_path, "r") as hf:
            embeddings = hf["embeddings"][...]
        hf.close()
        return embeddings
    except Exception as e:
        logging.info(f"error in reading embedding h5 file: {e}", exc_info=True)


def load_index(index_path):
    try:
        logging.info(f"reading index file: {index_path}")
        index = faiss.read_index(index_path)
        return index
    except Exception as e:
        logging.error(f"Error in Indexing : {e}", exc_info=True)


def save_index(entity_type, partition_number):
    """Saves the index file 
    
    Arguments:
        entity_file {[str]} -- Name of the entity files
    
    Returns:
        [type] -- created index
    """
    try:
        index_filename = f"index_{entity_type}_{partition_number}.index"
        index_path = os.path.join(CHECKPOINT_DIRECTORY, "index", index_filename)
        embeddings = read_embeddings(entity_type, partition_number)

        if not os.path.exists(index_path):
            logging.info(f"creating new index file {index_filename}")
            index = create_faiss_index()
            if FAISS_INDEX_NAME == "IndexIVFFlat":
                index.train(embeddings)
                index.add(embeddings)
                faiss.write_index(index, index_path)
        else:
            logging.info("index exists ")

    except Exception as e:
        logging.info(f"error in index creation: {e}", exc_info=True)


def create_indexes():
    try:
        initialise_config()
        logging.info(
            f"-------------------------CHECKING FOR INDEXES------------------------"
        )
        create_index_directory()
        with open(os.path.join(DATA_DIRECTORY, "entity_dictionary.json"), "r") as f:
            all_entity_dictionary = json.load(f)
        f.close()
        for ent in all_entity_dictionary["all_entities"]:
            try:
                partition_number = ent["partition_number"]
                entity_type = ent["entity_type"]
                save_index(entity_type, partition_number)
            except Exception as e:
                logging.info(f"error in index creation: {e}", exc_info=True)
                continue
        logging.info("Done")
    except Exception as e:
        logging.info(f"error in index creation: {e}", exc_info=True)


def search_in_index(index_filename, query_entity_embedding):
    try:
        index_path = os.path.join(CHECKPOINT_DIRECTORY, "index", index_filename)
        index = load_index(index_path)
        distances, indices = index.search(query_entity_embedding, neighbors)
        return distances, indices
    except Exception as e:
        logging.info(f"{e}", exc_info=True)


def search_all(entity_type, partition_number, query_index):
    initialise_config()
    entity_file_list = []
    embeddings = read_embeddings(entity_type, partition_number)
    query_entity_embedding = embeddings[query_index, :]
    query_entity_embedding = query_entity_embedding.reshape((1, EMBEDDING_DIMENSIONS))
    with open(os.path.join(DATA_DIRECTORY, "entity_dictionary.json"), "r") as f:
        all_entity_dictionary = json.load(f)
    f.close()
    search_results = np.empty((0, 3))
    for i, ent in enumerate(all_entity_dictionary["all_entities"]):
        try:
            partition_number = ent["partition_number"]
            entity_type = ent["entity_type"]
            entity_file_list.append(f"{entity_type}_{partition_number}")
            index_filename = f"index_{entity_type}_{partition_number}.index"
            distances, indices = search_in_index(index_filename, query_entity_embedding)
            distances = distances.reshape((-1, 1))
            indices = indices.reshape((-1, 1))
            list_id = np.array([i] * len(indices)).reshape(-1, 1)
            result = np.concatenate((indices, distances, list_id), axis=1)
            search_results = np.vstack([search_results, result])
        except Exception as e:
            logging.info(f"Skipping search due to : {e}", exc_info=True)
            continue
    search_results = search_results[search_results[:, 1].argsort()]
    return search_results, entity_file_list, neighbors
