from embeoj.export import export
from embeoj.preprocess import preprocess_exported_data
from embeoj.train import convert_tsv_to_pbg


if __name__ == "__main__":
    print("exporting graph data, creating config files ")
    export()
    print("converting to tsv")
    preprocess_exported_data()
    print("converting to pbg format")
    convert_tsv_to_pbg()
