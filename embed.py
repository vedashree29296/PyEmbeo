from embeoj.export import export
from embeoj.preprocess import preprocess_exported_data
from embeoj.train import convert_tsv_to_pbg, train_embeddings
from embeoj.tasks.similarity_search import similarity_search
from embeoj.utils import update_config, test_db_connection
import click


@click.command()
@click.option("--config_path", default=None, help="path to a yml configuration file")
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
@click.option(
    "--task", type=click.Choice(["train", "similarity_search"], case_sensitive=False)
)
def embed(config_path, project_name, url, username, password, task):
    """Command line entry function for all the functions
    """
    try:
        # test run to check for db connection
        if not test_db_connection():
            return
        if task == "train":
            update_config(
                config_path=config_path,
                project_name=project_name,
                neo4j_url=url,
                neo4j_user=username,
                neo4j_password=password,
            )

            export()
            preprocess_exported_data()
            convert_tsv_to_pbg()
            train_embeddings()
        else:
            entity_name = "21621"
            similarity_search(entity_name)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    embed()
