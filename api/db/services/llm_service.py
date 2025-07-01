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
"""
LLM服务管理系统

概述：
该模块实现了一个多租户的大语言模型服务管理系统，包括：
1. LLM工厂和模型的数据库操作服务
2. 租户级别的LLM配置和授权管理
3. 统一的LLM调用接口封装
4. 使用量统计和Langfuse监控集成
5. 支持多种类型的AI模型（聊天、嵌入、重排序、语音转文本、文本转语音、图像识别等）
"""
import logging

from langfuse import Langfuse

from api import settings
from api.db import LLMType
from api.db.db_models import DB, LLM, LLMFactories, TenantLLM
from api.db.services.common_service import CommonService
from api.db.services.langfuse_service import TenantLangfuseService
from api.db.services.user_service import TenantService
from rag.llm import ChatModel, CvModel, EmbeddingModel, RerankModel, Seq2txtModel, TTSModel


class LLMFactoriesService(CommonService):
    """
        概述：LLM工厂服务类，管理各种LLM提供商的信息

        处理步骤：
        - 继承通用服务类，提供基础的CRUD操作

        输入：无特殊输入
        输出：LLMFactories数据库操作接口
        """
    model = LLMFactories


class LLMService(CommonService):
    """
       概述：LLM模型服务类，管理具体的LLM模型信息

       处理步骤：
       - 继承通用服务类，提供基础的CRUD操作

       输入：无特殊输入
       输出：LLM数据库操作接口
       """
    model = LLM


class TenantLLMService(CommonService):
    """
        概述：租户LLM服务类，管理租户级别的LLM配置和使用

        主要功能：
        1. 租户LLM API密钥管理
        2. 模型名称和工厂的解析
        3. 模型配置获取和实例化
        4. 使用量统计更新
        """
    model = TenantLLM

    @classmethod
    @DB.connection_context()
    def get_api_key(cls, tenant_id, model_name):
        """
               概述：获取指定租户和模型的API密钥配置

               处理步骤：
               1. 解析模型名称，分离模型名和工厂名
               2. 根据是否有工厂名，构造不同的查询条件
               3. 查询租户LLM配置表
               4. 返回第一个匹配的配置

               输入：
               - tenant_id: 租户ID
               - model_name: 模型名称（可能包含@factory格式）

               输出：
               - TenantLLM对象或None
               """
        mdlnm, fid = TenantLLMService.split_model_name_and_factory(model_name)
        if not fid:
            objs = cls.query(tenant_id=tenant_id, llm_name=mdlnm)
        else:
            objs = cls.query(tenant_id=tenant_id, llm_name=mdlnm, llm_factory=fid)
        if not objs:
            return
        return objs[0]

    @classmethod
    @DB.connection_context()
    def get_my_llms(cls, tenant_id):
        """
               概述：获取指定租户的所有已配置LLM列表

               处理步骤：
               1. 构造查询字段列表（工厂、logo、标签、模型类型、名称、使用量）
               2. 关联LLMFactories表获取工厂信息
               3. 过滤条件：租户ID匹配且API密钥不为空
               4. 返回字典格式的结果列表

               输入：
               - tenant_id: 租户ID

               输出：
               - 包含LLM信息的字典列表
               """
        fields = [cls.model.llm_factory, LLMFactories.logo, LLMFactories.tags, cls.model.model_type, cls.model.llm_name, cls.model.used_tokens]
        objs = cls.model.select(*fields).join(LLMFactories, on=(cls.model.llm_factory == LLMFactories.name)).where(cls.model.tenant_id == tenant_id, ~cls.model.api_key.is_null()).dicts()

        return list(objs)

    @staticmethod
    def split_model_name_and_factory(model_name):
        """
               概述：解析模型名称，分离出模型名和工厂名

               处理步骤：
               1. 按@符号分割模型名称
               2. 如果没有@符号，返回原模型名和None
               3. 如果有多个@符号，将前面部分作为模型名，最后部分作为工厂名
               4. 验证工厂名是否在配置的提供商列表中
               5. 异常处理，确保返回有效结果

               输入：
               - model_name: 模型名称字符串（格式：model_name 或 model_name@factory）

               输出：
               - (model_name, factory_name) 元组，factory_name可能为None
               """
        arr = model_name.split("@")
        if len(arr) < 2:
            return model_name, None
        if len(arr) > 2:
            return "@".join(arr[0:-1]), arr[-1]

        # model name must be xxx@yyy
        try:
            model_factories = settings.FACTORY_LLM_INFOS
            model_providers = set([f["name"] for f in model_factories])
            if arr[-1] not in model_providers:
                return model_name, None
            return arr[0], arr[-1]
        except Exception as e:
            logging.exception(f"TenantLLMService.split_model_name_and_factory got exception: {e}")
        return model_name, None

    @classmethod
    @DB.connection_context()
    def get_model_config(cls, tenant_id, llm_type, llm_name=None):
        """
               概述：获取指定租户和类型的模型配置信息

               处理步骤：
               1. 获取租户信息，验证租户存在性
               2. 根据LLM类型确定默认模型名称（从租户配置中获取）
               3. 获取模型的API密钥配置
               4. 处理工厂名不匹配的情况（兼容性处理）
               5. 合并LLM基本信息（如工具支持能力）
               6. 处理特殊情况：本地模型和开源模型的配置
               7. 返回完整的模型配置字典

               输入：
               - tenant_id: 租户ID
               - llm_type: LLM类型（聊天、嵌入、重排序等）
               - llm_name: 可选的模型名称（如果不提供则使用租户默认配置）

               输出：
               - 包含模型配置信息的字典（api_key, llm_factory, llm_name, api_base, is_tools等）

               异常：
               - LookupError: 租户不存在、模型类型未设置或模型未授权
               """
        e, tenant = TenantService.get_by_id(tenant_id)
        if not e:
            raise LookupError("Tenant not found")

        # 根据LLM类型获取对应的默认模型名称
        if llm_type == LLMType.EMBEDDING.value:
            mdlnm = tenant.embd_id if not llm_name else llm_name
        elif llm_type == LLMType.SPEECH2TEXT.value:
            mdlnm = tenant.asr_id
        elif llm_type == LLMType.IMAGE2TEXT.value:
            mdlnm = tenant.img2txt_id if not llm_name else llm_name
        elif llm_type == LLMType.CHAT.value:
            mdlnm = tenant.llm_id if not llm_name else llm_name
        elif llm_type == LLMType.RERANK:
            mdlnm = tenant.rerank_id if not llm_name else llm_name
        elif llm_type == LLMType.TTS:
            mdlnm = tenant.tts_id if not llm_name else llm_name
        else:
            assert False, "LLM type error"

        # 获取模型配置
        model_config = cls.get_api_key(tenant_id, mdlnm)
        mdlnm, fid = TenantLLMService.split_model_name_and_factory(mdlnm)
        # 处理工厂名不匹配的情况
        if not model_config:  # for some cases seems fid mismatch
            model_config = cls.get_api_key(tenant_id, mdlnm)
        if model_config:
            model_config = model_config.to_dict()
            # 获取模型的工具支持能力
            llm = LLMService.query(llm_name=mdlnm) if not fid else LLMService.query(llm_name=mdlnm, fid=fid)
            if not llm and fid:  # for some cases seems fid mismatch
                llm = LLMService.query(llm_name=mdlnm)
            if llm:
                model_config["is_tools"] = llm[0].is_tools

        # 处理特殊情况：本地模型和开源模型
        if not model_config:
            if llm_type in [LLMType.EMBEDDING, LLMType.RERANK]:
                llm = LLMService.query(llm_name=mdlnm) if not fid else LLMService.query(llm_name=mdlnm, fid=fid)
                if llm and llm[0].fid in ["Youdao", "FastEmbed", "BAAI"]:
                    model_config = {"llm_factory": llm[0].fid, "api_key": "", "llm_name": mdlnm, "api_base": ""}
            if not model_config:
                if mdlnm == "flag-embedding":
                    model_config = {"llm_factory": "Tongyi-Qianwen", "api_key": "", "llm_name": llm_name, "api_base": ""}
                else:
                    if not mdlnm:
                        raise LookupError(f"Type of {llm_type} model is not set.")
                    raise LookupError("Model({}) not authorized".format(mdlnm))
        return model_config

    @classmethod
    @DB.connection_context()
    def model_instance(cls, tenant_id, llm_type, llm_name=None, lang="Chinese"):
        """
               概述：创建指定类型的模型实例

               处理步骤：
               1. 获取模型配置信息
               2. 根据LLM类型选择对应的模型类
               3. 验证工厂是否支持该类型的模型
               4. 使用配置信息实例化模型对象
               5. 返回模型实例

               输入：
               - tenant_id: 租户ID
               - llm_type: LLM类型
               - llm_name: 可选的模型名称
               - lang: 语言设置，默认为中文

               输出：
               - 对应类型的模型实例对象，如果不支持则返回None
               """
        model_config = TenantLLMService.get_model_config(tenant_id, llm_type, llm_name)
        if llm_type == LLMType.EMBEDDING.value:
            if model_config["llm_factory"] not in EmbeddingModel:
                return
            return EmbeddingModel[model_config["llm_factory"]](model_config["api_key"], model_config["llm_name"], base_url=model_config["api_base"])

        if llm_type == LLMType.RERANK:
            if model_config["llm_factory"] not in RerankModel:
                return
            return RerankModel[model_config["llm_factory"]](model_config["api_key"], model_config["llm_name"], base_url=model_config["api_base"])

        if llm_type == LLMType.IMAGE2TEXT.value:
            if model_config["llm_factory"] not in CvModel:
                return
            return CvModel[model_config["llm_factory"]](model_config["api_key"], model_config["llm_name"], lang, base_url=model_config["api_base"])

        if llm_type == LLMType.CHAT.value:
            if model_config["llm_factory"] not in ChatModel:
                return
            return ChatModel[model_config["llm_factory"]](model_config["api_key"], model_config["llm_name"], base_url=model_config["api_base"])

        if llm_type == LLMType.SPEECH2TEXT:
            if model_config["llm_factory"] not in Seq2txtModel:
                return
            return Seq2txtModel[model_config["llm_factory"]](key=model_config["api_key"], model_name=model_config["llm_name"], lang=lang, base_url=model_config["api_base"])
        if llm_type == LLMType.TTS:
            if model_config["llm_factory"] not in TTSModel:
                return
            return TTSModel[model_config["llm_factory"]](
                model_config["api_key"],
                model_config["llm_name"],
                base_url=model_config["api_base"],
            )

    @classmethod
    @DB.connection_context()
    def increase_usage(cls, tenant_id, llm_type, used_tokens, llm_name=None):
        """
               概述：增加指定租户和模型的使用量统计

               处理步骤：
               1. 获取租户信息，验证租户存在性
               2. 根据LLM类型映射到租户配置中的对应模型
               3. 解析模型名称和工厂名
               4. 更新数据库中的使用量字段
               5. 异常处理和日志记录

               输入：
               - tenant_id: 租户ID
               - llm_type: LLM类型
               - used_tokens: 使用的token数量
               - llm_name: 可选的模型名称

               输出：
               - 更新影响的行数，失败时返回0
               """
        e, tenant = TenantService.get_by_id(tenant_id)
        if not e:
            logging.error(f"Tenant not found: {tenant_id}")
            return 0
        # 根据LLM类型映射到对应的模型配置
        llm_map = {
            LLMType.EMBEDDING.value: tenant.embd_id if not llm_name else llm_name,
            LLMType.SPEECH2TEXT.value: tenant.asr_id,
            LLMType.IMAGE2TEXT.value: tenant.img2txt_id,
            LLMType.CHAT.value: tenant.llm_id if not llm_name else llm_name,
            LLMType.RERANK.value: tenant.rerank_id if not llm_name else llm_name,
            LLMType.TTS.value: tenant.tts_id if not llm_name else llm_name,
        }

        mdlnm = llm_map.get(llm_type)
        if mdlnm is None:
            logging.error(f"LLM type error: {llm_type}")
            return 0

        llm_name, llm_factory = TenantLLMService.split_model_name_and_factory(mdlnm)

        try:
            # 更新使用量
            num = (
                cls.model.update(used_tokens=cls.model.used_tokens + used_tokens)
                .where(cls.model.tenant_id == tenant_id, cls.model.llm_name == llm_name, cls.model.llm_factory == llm_factory if llm_factory else True)
                .execute()
            )
        except Exception:
            logging.exception("TenantLLMService.increase_usage got exception,Failed to update used_tokens for tenant_id=%s, llm_name=%s", tenant_id, llm_name)
            return 0

        return num

    @classmethod
    @DB.connection_context()
    def get_openai_models(cls):
        """
                概述：获取所有OpenAI模型列表（排除特定的嵌入模型）

                处理步骤：
                1. 查询LLM工厂为OpenAI的所有模型
                2. 排除text-embedding-3-small和text-embedding-3-large模型
                3. 返回字典格式的结果列表

                输入：无

                输出：
                - OpenAI模型信息的字典列表
                """
        objs = cls.model.select().where((cls.model.llm_factory == "OpenAI"), ~(cls.model.llm_name == "text-embedding-3-small"), ~(cls.model.llm_name == "text-embedding-3-large")).dicts()
        return list(objs)


class LLMBundle:
    """
       概述：LLM捆绑类，提供统一的LLM调用接口和监控功能

       主要功能：
       1. 封装各种类型的LLM操作（聊天、嵌入、重排序、语音转文本等）
       2. 自动处理使用量统计
       3. 集成Langfuse监控和追踪
       4. 提供工具调用支持
       5. 处理推理内容过滤
       """
    def __init__(self, tenant_id, llm_type, llm_name=None, lang="Chinese"):
        """
                概述：初始化LLM捆绑实例

                处理步骤：
                1. 保存初始化参数
                2. 创建模型实例
                3. 验证模型实例创建成功
                4. 获取模型配置信息
                5. 设置最大长度和工具支持标志
                6. 初始化Langfuse监控（如果配置存在）

                输入：
                - tenant_id: 租户ID
                - llm_type: LLM类型
                - llm_name: 可选的模型名称
                - lang: 语言设置

                输出：无（构造函数）

                异常：
                - AssertionError: 模型实例创建失败
                """
        self.tenant_id = tenant_id
        self.llm_type = llm_type
        self.llm_name = llm_name
        self.mdl = TenantLLMService.model_instance(tenant_id, llm_type, llm_name, lang=lang)
        assert self.mdl, "Can't find model for {}/{}/{}".format(tenant_id, llm_type, llm_name)
        model_config = TenantLLMService.get_model_config(tenant_id, llm_type, llm_name)
        self.max_length = model_config.get("max_tokens", 8192)

        self.is_tools = model_config.get("is_tools", False)

        # 初始化Langfuse监控
        langfuse_keys = TenantLangfuseService.filter_by_tenant(tenant_id=tenant_id)
        if langfuse_keys:
            langfuse = Langfuse(public_key=langfuse_keys.public_key, secret_key=langfuse_keys.secret_key, host=langfuse_keys.host)
            if langfuse.auth_check():
                self.langfuse = langfuse
                self.trace = self.langfuse.trace(name=f"{self.llm_type}-{self.llm_name}")
        else:
            self.langfuse = None

    def bind_tools(self, toolcall_session, tools):
        """
               概述：绑定工具到模型实例

               处理步骤：
               1. 检查模型是否支持工具调用
               2. 如果不支持，记录警告日志并返回
               3. 如果支持，调用模型的bind_tools方法

               输入：
               - toolcall_session: 工具调用会话
               - tools: 工具列表

               输出：无
               """
        if not self.is_tools:
            logging.warning(f"Model {self.llm_name} does not support tool call, but you have assigned one or more tools to it!")
            return
        self.mdl.bind_tools(toolcall_session, tools)

    def encode(self, texts: list):
        """
                概述：文本编码为向量

                处理步骤：
                1. 创建Langfuse生成记录（如果启用）
                2. 调用模型的encode方法
                3. 更新使用量统计
                4. 记录监控信息
                5. 返回编码结果

                输入：
                - texts: 待编码的文本列表

                输出：
                - (embeddings, used_tokens) 元组
                """
        if self.langfuse:
            generation = self.trace.generation(name="encode", model=self.llm_name, input={"texts": texts})

        embeddings, used_tokens = self.mdl.encode(texts)
        llm_name = getattr(self, "llm_name", None)
        if not TenantLLMService.increase_usage(self.tenant_id, self.llm_type, used_tokens, llm_name):
            logging.error("LLMBundle.encode can't update token usage for {}/EMBEDDING used_tokens: {}".format(self.tenant_id, used_tokens))

        if self.langfuse:
            generation.end(usage_details={"total_tokens": used_tokens})

        return embeddings, used_tokens

    def encode_queries(self, query: str):
        """
                概述：查询文本编码为向量

                处理步骤：
                1. 创建Langfuse生成记录（如果启用）
                2. 调用模型的encode_queries方法
                3. 更新使用量统计
                4. 记录监控信息
                5. 返回编码结果

                输入：
                - query: 待编码的查询文本

                输出：
                - (embedding, used_tokens) 元组
                """
        if self.langfuse:
            generation = self.trace.generation(name="encode_queries", model=self.llm_name, input={"query": query})

        emd, used_tokens = self.mdl.encode_queries(query)
        llm_name = getattr(self, "llm_name", None)
        if not TenantLLMService.increase_usage(self.tenant_id, self.llm_type, used_tokens, llm_name):
            logging.error("LLMBundle.encode_queries can't update token usage for {}/EMBEDDING used_tokens: {}".format(self.tenant_id, used_tokens))

        if self.langfuse:
            generation.end(usage_details={"total_tokens": used_tokens})

        return emd, used_tokens

    def similarity(self, query: str, texts: list):
        """
                概述：计算查询与文本列表的相似度

                处理步骤：
                1. 创建Langfuse生成记录（如果启用）
                2. 调用模型的similarity方法
                3. 更新使用量统计
                4. 记录监控信息
                5. 返回相似度结果

                输入：
                - query: 查询文本
                - texts: 待比较的文本列表

                输出：
                - (similarities, used_tokens) 元组
                """
        if self.langfuse:
            generation = self.trace.generation(name="similarity", model=self.llm_name, input={"query": query, "texts": texts})

        sim, used_tokens = self.mdl.similarity(query, texts)
        if not TenantLLMService.increase_usage(self.tenant_id, self.llm_type, used_tokens):
            logging.error("LLMBundle.similarity can't update token usage for {}/RERANK used_tokens: {}".format(self.tenant_id, used_tokens))

        if self.langfuse:
            generation.end(usage_details={"total_tokens": used_tokens})

        return sim, used_tokens

    def describe(self, image, max_tokens=300):
        """
                概述：描述图像内容

                处理步骤：
                1. 创建Langfuse生成记录（如果启用）
                2. 调用模型的describe方法
                3. 更新使用量统计
                4. 记录监控信息
                5. 返回描述文本

                输入：
                - image: 图像数据
                - max_tokens: 最大token数（暂未使用）

                输出：
                - 图像描述文本
                """
        if self.langfuse:
            generation = self.trace.generation(name="describe", metadata={"model": self.llm_name})

        txt, used_tokens = self.mdl.describe(image)
        if not TenantLLMService.increase_usage(self.tenant_id, self.llm_type, used_tokens):
            logging.error("LLMBundle.describe can't update token usage for {}/IMAGE2TEXT used_tokens: {}".format(self.tenant_id, used_tokens))

        if self.langfuse:
            generation.end(output={"output": txt}, usage_details={"total_tokens": used_tokens})

        return txt

    def describe_with_prompt(self, image, prompt):
        """
                概述：基于指定提示描述图像内容

                处理步骤：
                1. 创建Langfuse生成记录（如果启用）
                2. 调用模型的describe_with_prompt方法
                3. 更新使用量统计
                4. 记录监控信息
                5. 返回描述文本

                输入：
                - image: 图像数据
                - prompt: 描述提示

                输出：
                - 图像描述文本
                """
        if self.langfuse:
            generation = self.trace.generation(name="describe_with_prompt", metadata={"model": self.llm_name, "prompt": prompt})

        txt, used_tokens = self.mdl.describe_with_prompt(image, prompt)
        if not TenantLLMService.increase_usage(self.tenant_id, self.llm_type, used_tokens):
            logging.error("LLMBundle.describe can't update token usage for {}/IMAGE2TEXT used_tokens: {}".format(self.tenant_id, used_tokens))

        if self.langfuse:
            generation.end(output={"output": txt}, usage_details={"total_tokens": used_tokens})

        return txt

    def transcription(self, audio):
        """
               概述：音频转文字

               处理步骤：
               1. 创建Langfuse生成记录（如果启用）
               2. 调用模型的transcription方法
               3. 更新使用量统计
               4. 记录监控信息
               5. 返回转录文本

               输入：
               - audio: 音频数据

               输出：
               - 转录文本
               """
        if self.langfuse:
            generation = self.trace.generation(name="transcription", metadata={"model": self.llm_name})

        txt, used_tokens = self.mdl.transcription(audio)
        if not TenantLLMService.increase_usage(self.tenant_id, self.llm_type, used_tokens):
            logging.error("LLMBundle.transcription can't update token usage for {}/SEQUENCE2TXT used_tokens: {}".format(self.tenant_id, used_tokens))

        if self.langfuse:
            generation.end(output={"output": txt}, usage_details={"total_tokens": used_tokens})

        return txt

    def tts(self, text):
        """
                概述：文字转语音（流式生成）

                处理步骤：
                1. 创建Langfuse span记录（如果启用）
                2. 调用模型的tts方法（生成器）
                3. 迭代处理音频块和token统计
                4. 更新使用量统计
                5. 结束监控记录

                输入：
                - text: 待转换的文本

                输出：
                - 音频数据块的生成器
                """
        if self.langfuse:
            span = self.trace.span(name="tts", input={"text": text})

        for chunk in self.mdl.tts(text):
            if isinstance(chunk, int):
                if not TenantLLMService.increase_usage(self.tenant_id, self.llm_type, chunk, self.llm_name):
                    logging.error("LLMBundle.tts can't update token usage for {}/TTS".format(self.tenant_id))
                return
            yield chunk

        if self.langfuse:
            span.end()

    def _remove_reasoning_content(self, txt: str) -> str:
        """
                概述：移除文本中的推理reasoning内容标签

                处理步骤：
                1. 查找第一个<think>标签的位置
                2. 查找最后一个</think>标签的位置
                3. 验证标签的有效性（结束标签在开始标签之后）
                4. 移除从开始到结束标签之间的所有内容
                5. 返回处理后的文本

                输入：
                - txt: 包含推理标签的原始文本

                输出：
                - 移除推理内容后的文本
                """
        first_think_start = txt.find("<think>")
        if first_think_start == -1:
            return txt

        last_think_end = txt.rfind("</think>")
        if last_think_end == -1:
            return txt

        if last_think_end < first_think_start:
            return txt

        return txt[last_think_end + len("</think>") :]

    def chat(self, system, history, gen_conf):
        """
                概述：聊天对话

                处理步骤：
                1. 创建Langfuse生成记录（如果启用）
                2. 根据工具支持情况选择对应的聊天方法
                3. 调用模型进行对话生成
                4. 移除推理内容标签
                5. 更新使用量统计
                6. 记录监控信息
                7. 返回对话结果

                输入：
                - system: 系统提示
                - history: 对话历史
                - gen_conf: 生成配置

                输出：
                - 生成的回复文本
                """
        if self.langfuse:
            generation = self.trace.generation(name="chat", model=self.llm_name, input={"system": system, "history": history})

        # 根据工具支持情况选择聊天方法
        chat = self.mdl.chat
        if self.is_tools and self.mdl.is_tools:
            chat = self.mdl.chat_with_tools

        txt, used_tokens = chat(system, history, gen_conf)
        txt = self._remove_reasoning_content(txt)

        if isinstance(txt, int) and not TenantLLMService.increase_usage(self.tenant_id, self.llm_type, used_tokens, self.llm_name):
            logging.error("LLMBundle.chat can't update token usage for {}/CHAT llm_name: {}, used_tokens: {}".format(self.tenant_id, self.llm_name, used_tokens))

        if self.langfuse:
            generation.end(output={"output": txt}, usage_details={"total_tokens": used_tokens})

        return txt

    def chat_streamly(self, system, history, gen_conf):
        """
                概述：流式聊天对话

                处理步骤：
                1. 创建Langfuse生成记录（如果启用）
                2. 初始化答案累积器和token计数器
                3. 根据工具支持情况选择对应的流式聊天方法
                4. 迭代处理流式响应
                5. 处理推理内容标签的移除
                6. 累积完整答案并逐步输出
                7. 处理token统计和使用量更新
                8. 结束监控记录

                输入：
                - system: 系统提示
                - history: 对话历史
                - gen_conf: 生成配置

                输出：
                - 累积答案的生成器（流式输出）
                """
        if self.langfuse:
            generation = self.trace.generation(name="chat_streamly", model=self.llm_name, input={"system": system, "history": history})

        ans = ""
        chat_streamly = self.mdl.chat_streamly
        total_tokens = 0
        # 根据工具支持情况选择流式聊天方法
        if self.is_tools and self.mdl.is_tools:
            chat_streamly = self.mdl.chat_streamly_with_tools

        for txt in chat_streamly(system, history, gen_conf):
            # 处理token统计（当收到整数时表示结束）
            if isinstance(txt, int):
                total_tokens = txt
                if self.langfuse:
                    generation.end(output={"output": ans})
                break
            # 处理推理reasoning内容标签
            if txt.endswith("</think>"):
                ans = ans.rstrip("</think>")

            ans += txt
            yield ans

        # 更新使用量统计
        if total_tokens > 0:
            if not TenantLLMService.increase_usage(self.tenant_id, self.llm_type, txt, self.llm_name):
                logging.error("LLMBundle.chat_streamly can't update token usage for {}/CHAT llm_name: {}, content: {}".format(self.tenant_id, self.llm_name, txt))
