#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import os
import logging
from api.utils import get_base_config, decrypt_database_config
from api.utils.file_utils import get_project_base_directory

# Server
RAG_CONF_PATH = os.path.join(get_project_base_directory(), "conf")

# Load datafile storage config from service_conf.yaml
STORAGE_IMPL_TYPE = get_base_config("storage_impl", "MINIO").upper()

# Determine storage implementation from config or environment
# config value may be lower case so normalize to upper case

DOC_ENGINE = os.getenv('DOC_ENGINE', 'elasticsearch')

ES = {}
INFINITY = {}
AZURE = {}
S3 = {}
MINIO = {}
OSS = {}
OS = {}

# Initialize the selected configuration data based on environment variables to solve the problem of initialization errors due to lack of configuration
if DOC_ENGINE == 'elasticsearch':
    ES = get_base_config("es", {})
elif DOC_ENGINE == 'opensearch':
    OS = get_base_config("os", {})
elif DOC_ENGINE == 'infinity':
    INFINITY = get_base_config("infinity", {"uri": "infinity:23817"})

if STORAGE_IMPL_TYPE in ['AZURE_SPN', 'AZURE_SAS']:
    AZURE = get_base_config("azure", {})
elif STORAGE_IMPL_TYPE == 'AWS_S3':
    S3 = get_base_config("s3", {})
elif STORAGE_IMPL_TYPE == 'MINIO':
    MINIO = decrypt_database_config(name="minio")
elif STORAGE_IMPL_TYPE == 'OSS':
    OSS = get_base_config("oss", {})
elif STORAGE_IMPL_TYPE == 'LOCAL':
    LOCAL_STORAGE_PATH = get_base_config("local_storage_path",
                                             os.path.join(get_project_base_directory(), "datafiles"))

# try:
#     REDIS = decrypt_database_config(name="redis")
# except Exception:
#     REDIS = {}
#     pass
REDIS = get_base_config("redis", {})

DOC_MAXIMUM_SIZE = int(os.environ.get("MAX_CONTENT_LENGTH", 128 * 1024 * 1024))
DOC_BULK_SIZE = int(os.environ.get("DOC_BULK_SIZE", 4))
EMBEDDING_BATCH_SIZE = int(os.environ.get("EMBEDDING_BATCH_SIZE", 16))
SVR_QUEUE_NAME = "rag_flow_svr_queue"
SVR_CONSUMER_GROUP_NAME = "rag_flow_svr_task_broker"
PAGERANK_FLD = "pagerank_fea"
# 标签字段名常量
TAG_FLD = "tag_feas"

PARALLEL_DEVICES = 0
try:
    import torch.cuda

    PARALLEL_DEVICES = torch.cuda.device_count()
    logging.info(f"found {PARALLEL_DEVICES} gpus")
except Exception:
    logging.info("can't import package 'torch'")


def print_rag_settings():
    logging.info(f"MAX_CONTENT_LENGTH: {DOC_MAXIMUM_SIZE}")
    logging.info(f"MAX_FILE_COUNT_PER_USER: {int(os.environ.get('MAX_FILE_NUM_PER_USER', 0))}")
    msg = f"****STORAGE_IMPL_TYPE: USING {STORAGE_IMPL_TYPE} STORAGE ****"
    logging.info(msg)
    if STORAGE_IMPL_TYPE == 'LOCAL':
        logging.info(f"Local storage path: {LOCAL_STORAGE_PATH}")
    elif STORAGE_IMPL_TYPE == 'AZURE_SPN' or STORAGE_IMPL_TYPE == 'AZURE_SAS':
        logging.info(f"Azure container_url: {AZURE['container_url']}")
    elif STORAGE_IMPL_TYPE == 'AWS_S3':
        logging.info(f"S3 region : {S3['region']}")
    elif STORAGE_IMPL_TYPE == 'MINIO':
        logging.info(f"Minio  host: {MINIO['host']}")
    elif STORAGE_IMPL_TYPE == 'OSS':
        logging.info(f"OSS  endpoint_url: {OSS['endpoint_url']},oss region:{OSS['region']},oss bucket:{OSS['bucket']}")


def get_svr_queue_name(priority: int) -> str:
    if priority == 0:
        return SVR_QUEUE_NAME
    return f"{SVR_QUEUE_NAME}_{priority}"


def get_svr_queue_names():
    return [get_svr_queue_name(priority) for priority in [1, 0]]
