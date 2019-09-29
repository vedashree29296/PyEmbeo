# PyEmbeo

### (Graphs embeddings for Neo4j in Python)

## INTRODUCTION
### NEO4J

Graphs databases are a powerful way to represent real world data in a simple and intuitive manner They can effectively capture inherent relationships within the data and provide meaningful insights that cannot be obtained using traditional relational databases. 

__Neo4j__ is a leading graph database platform with a great community support that offers great capabilities for storing and querying large scale enterprise data.

 
### WHAT ARE GRAPH EMBEDDINGS?
Machine Learning on graph data has been the talk of the town for quite a while now. With the advantage of using graphs being quite evident; applying machine learning algorithms on graphs can be used for tasks such as graph analysis, link prediction, clustering etc.

__Graph Embeddings__ are a way to encode the graph data as vectors that can effectively capture the structural information, such as the graph topology and the node to node relationships in the graph database. These embeddings can then be ingested by ML algorithms for performing various tasks

### HOW CAN GRAPH EMBEDDINGS BE USED?
Graph embeddings can be used to perform various tasks including machine learning tasks.
For example, embeddings of two nodes can be used to determine if a relationship can exist between them. Or, given a particular node and a relation, embeddings can be used to find similar nodes and rank them using similarity search algortihms
Common applications include  __knowledge graph completion__ and __drug discovery__ where new relations can be dicovered between two nodes. __Link prediction__ and  __Recommendation systems__ in cases such as social networks analysis where potential new friendships can be found.

## PyEmbeo

PyEmbeo is a project in python that creates graph embeddings for a Neo4j graph database.
Link to the neo4j database can be passed to the script through a command line interface to generate graph embeddings. 
Other parameters (such as the number of epochs for training) can be configured by creating or editing the __"config.yml"__ file. (See config_link for all the configurable parameters).
The obtained embeddings can be then used to perform other tasks such as similarity search, scoring or ranking. (Note: currently the similarity search task has been implemented, other tasks are still in development)


### Installation and Setup
***

#### REQUIREMENTS

- Neo4j database and py2neo

- conda (or miniconda)

- python >=3.5

Also, ensure that the __APOC__ plugin for Neo4j is installed and configured for your database. Make sure following lines are added to the __'neo4j.conf'__ file:

`apoc.import.file.enabled=true`  .

`apoc.export.file.enabled=true`  .

`dbms.security.procedures.whitelist=apoc.*`  .

`apoc.import.file.use_neo4j_config=false`  .


#### STEPS FOR INSTALLATION:

- Clone the repository using and navigate inside the directory :

`git clone  <link>`  

` cd ./PyEmbeo`  


- create a conda environment and activate it by running:

`conda env create -f requirements.yml`
- This creates a conda environment called pyembeo and installs all the requirements.  Activate the environment by exceuting:

`conda activate pyembeo`

## Usage

***
### Training:

PyEmbeo uses torchbiggraph to generate graph embeddings. PyTorch-BigGraph is a tool can create graph embeddings for very large, multi-realtional graphs without the need for computing resources such as GPUs.
For more details,you can refer to the [PyTorch-BigGraph documentation](https://torchbiggraph.readthedocs.io/en/latest/index.html)

The script uses the __config.yml__ file to configure all the training parameters. The file has been preconfigured with default parameters and only a minimal set of parameter need to be passed through the command line. However, the parameters can be tweaked by editing the config.yml file.

The command line interface takes the following parameters:

- __project_name__ : This is the root directory that will store the required data and embedding checkpoint files.

- __url__ : The url to the neo4j database in the format of bolt(or http): // (ip of the database):(port number). By default the url is configured to __bolt://localhost:7687__ 

You will be then prompted to enter the username and password to connect to the database.
 
- __config_path__: This is an optional parameter that specifies the path to a 'config.yml' file incase the default parameters are edited.

### Similarity Search:

A common task using graph embeddings is performing similarity search to return similar nodes which can then be used to find undiscovered relationships.

PyEmbeo uses FAISS that is used for fast similarity searching for a large number of vectors. A similarity search can be triggered by passing the node id of a particular node (any even any other property can also be passed but it will be computationally heavy) along with the --task option in the command line interface.

More Details can be found at: [official documentation](https://github.com/facebookresearch/faiss/wiki) or [this post](https://towardsdatascience.com/understanding-faiss-619bb6db2d1a) and [this post](https://medium.com/dotstar/understanding-faiss-part-2-79d90b1e5388)



## Storage format:
A root directory with the name given by the **--project_name** argument is created along with its subfolders:
|-- my_project_name/  .

|------ data/  .

|---------- graph_partitioned/  .

|----------------- egdes.h5 files  .

|---------- files related to the nodes (.json,.txt,.tsv files)  .

|------ model/  

|---------- index/  

|----------------- .index files  

|---------- config.json  

|---------- embeddings files (.h5 and .txt files)  

|------ metadata.json  


**data/** : stores all the data related files such as 
- entity_names (.json) stores list of the node ids of the entities
- entity count (.txt) store the total count of entites
- graph.tsv stores the graph data in tsv format which is used as an input for training graph embeddings
- graph_partitioned/ edges (.h5) files store the edge list

**model/**: stores the checkpoint and embeddings files created during training.
- config.json is a configuration file that is created using the config.yml file which is used by torchbiggraph for trainig
- embeddings (.h5) store the graph embeddings 
- checkpoint_version(.txt) stores the latest checkpoint version of the embeddings

**metadata.json**  stores data aboout the number of nodes, labels and types of relationships

## Configuration Options:

Default parameters can be overridden by editing or creating a config.yml file. Most of the parameters are used by torchbiggraph and more details about each can be found at :.........
Some of the editable paramters list includes:

- **EMBEDDING_DIMENSIONS**: size of the embedding vectors. defaults to 400
- **EPOCHS**: number of training iterations to perform (defaults to 20)

- **NUM_PARTITIONS** : the number of partitions to divide the nodes into. This is used in torchbiggraph which will divide the nodes of a particular type. (defaults to 1)

torchbiggraph uses the concept of operators and comparators for scoring while training the graph embeddings. More details can be found at: [comparators and operators](https://torchbiggraph.readthedocs.io/en/latest/scoring.html)
- **operator** : can be 'none','diagonal','translation','complex_diagonal', 'affine' or 'linear' . Defaults to 'complex_diagonal'
- **comparator** :can be 'dot','cos','l2','squared_l2'. Defaults to 'dot'

The similarity search parameters can also be tweaked accordingly:
- **FAISS_INDEX_NAME**: The type of index to use for similarity searching . Defaults to IndexIVFFlat. Currently only the IVFFlat and FlatL2 index types are supported . see [index types](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes) for details on type of indexes
- **NEAREST_NEIGHBORS**: number of similar nodes to return. Defaults ti 5
- **NUM_CLUSTER**: number of clusters that are created by the clustering algorithm while creating the index

