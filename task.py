from embeoj.tasks.similarity_search import similarity_search
from embeoj.utils import test_db_connection, logging, update_config
import click
import sys


@click.command()
@click.argument("task")
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
@click.option("--node", default=None, help="node id of any node in the graph")
@click.option("--config_path", default=None, help="path to a yml config file")
def tasks(task, project_name, url, username, password, node, config_path):
    """Command line interface for similarity search on graph embeddings
    """
    try:
        if not test_db_connection():
            logging.info("could not connect to Neo4j")
            return
        update_config(
            config_path=config_path,
            project_name=project_name,
            neo4j_url=url,
            neo4j_user=username,
            neo4j_password=password,
        )
        if node is None:
            logging.info("Enter node id!!")
            sys.exit()
        if task == "similarity":
            similarity_search(node)
    except Exception as e:
        logging.info(f"error: {e}", exc_info=True)
        sys.exit(e)


if __name__ == "__main__":
    tasks()
