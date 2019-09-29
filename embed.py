from embeoj.export import export
from embeoj.preprocess import preprocess_exported_data
from embeoj.train import convert_tsv_to_pbg, train_embeddings
from embeoj.utils import update_config, test_db_connection, logging
import click
import sys


@click.command()
@click.argument("train")
@click.option(
    "--project_name",
    default="myproject",
    help="name of the root folder where embeddings are stored",
    show_default=True,
)
@click.option(
    "--url",
    default="bolt://localhost:7687/",
    help="url for neo4j database",
    show_default=True,
)
@click.option(
    "--username",
    default="neo4j",
    help="username for neo4j database",
    show_default=True,
    prompt=True,
)
@click.option(
    "--password",
    default="neo4j",
    help="password for neo4j database",
    prompt=True,
    hide_input=True,
)
@click.option("--config_path", default=None, help="path to a yml configuration file")
def embed(config_path, project_name, url, username, password, train):
    """Command line interface for training and generating graph embeddings
    """
    try:
        # test run to check for db connection
        if not test_db_connection():
            logging.info("could not connect to Neo4j")
            sys.exit()
            return
        if train == "train":
            update_config(
                config_path=config_path,
                project_name=project_name,
                neo4j_url=url,
                neo4j_user=username,
                neo4j_password=password,
            )
            export()  # export graph data to tsv json file
            preprocess_exported_data()  # convert to tsv file for biggraph to read
            convert_tsv_to_pbg()  # process data files for training
            train_embeddings()  # train
            logging.info("Done....")

    except Exception as e:
        logging.info(f"Error: {e}")
        sys.exit(e)


if __name__ == "__main__":
    embed()
