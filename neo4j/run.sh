export NEO4j_HOME_DIR="$(pwd)"
echo ${NEO4j_HOME_DIR}

docker run --rm \
    -e NEO4J_URI=document_graph \
    -e NEO4J_dbms_memory_heap_initial__size=512m \
    -e NEO4J_dbms_memory_heap_max__size=4G \
    -e NEO4J_dbms_memory_pagecache_size=2G \
    -e NEO4J_apoc.export.file.enabled=true \
    -e NEO4J_apoc_import_file_enabled=true \
    -e NEO4J_dbms_security_procedures_whitelist=apoc.* \
    -e NEO4J_AUTH=neo4j/test \
    -v ${NEO4j_HOME_DIR}/logs:/logs \
    -v ${NEO4j_HOME_DIR}/data:/var/lib/neo4j/data \
    -v ${NEO4j_HOME_DIR}/plugins:/var/lib/neo4j/plugins \
    -p 7474:7474 \
    -p 7687:7687 \
    -d neo4j:3.5.11