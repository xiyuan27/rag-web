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
import os.path
import logging
from logging.handlers import RotatingFileHandler

initialized_root_logger = False

def get_project_base_directory():
    PROJECT_BASE = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            os.pardir,
            os.pardir,
        )
    )
    return PROJECT_BASE

def init_root_logger(logfile_basename: str, log_format: str = "%(asctime)-15s %(levelname)-8s %(process)d %(message)s"):
    global initialized_root_logger
    if initialized_root_logger:
        return
    initialized_root_logger = True

    logger = logging.getLogger()
    logger.handlers.clear()

    logs_dir = os.path.abspath(os.path.join(get_project_base_directory(), "logs"))
    os.makedirs(logs_dir, exist_ok=True)
    formatter = logging.Formatter(log_format)

    # 1. INFO及以下级别日志文件 (info.log)
    info_log_path = os.path.join(logs_dir, f"{logfile_basename}_info.log")
    info_handler = RotatingFileHandler(info_log_path, maxBytes=10 * 1024 * 1024, backupCount=5)
    info_handler.setFormatter(formatter)
    info_handler.setLevel(logging.INFO)
    info_handler.addFilter(lambda record: record.levelno <= logging.INFO)
    logger.addHandler(info_handler)

    # 2. ERROR及以上级别日志文件 (error.log) - 包含完整堆栈
    error_log_path = os.path.join(logs_dir, f"{logfile_basename}_error.log")
    error_handler = RotatingFileHandler(error_log_path, maxBytes=10 * 1024 * 1024, backupCount=5)
    error_handler.setFormatter(logging.Formatter(
        "%(asctime)-15s %(levelname)-8s %(process)d %(pathname)s:%(lineno)d %(funcName)s() %(message)s"
    ))
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

    # 3. 控制台输出 (仅显示WARNING及以上)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)
    logger.addHandler(console_handler)

    # 4. 设置root logger级别
    logger.setLevel(logging.INFO)

    logging.captureWarnings(True)


def log_exception(e, *args):
    logging.exception(e)
    for a in args:
        logging.error(str(a))
    raise e