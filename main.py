from embeoj.export import export
from embeoj.preprocess import preprocess_exported_data
from embeoj.train import convert_tsv_to_pbg,train_embeddings
from embeoj.tasks.similarity_search import similarity_search

if __name__ == "__main__":
    export()
    preprocess_exported_data()
    convert_tsv_to_pbg()
    train_embeddings()
    # entity_name = "21621"
    # similarity_search(entity_name)
