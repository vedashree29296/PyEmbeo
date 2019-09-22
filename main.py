from embeoj.export import export
from embeoj.preprocess import preprocess_exported_data
from embeoj.train import convert_tsv_to_pbg


if __name__ == "__main__":
    export()
    preprocess_exported_data()
    convert_tsv_to_pbg()
