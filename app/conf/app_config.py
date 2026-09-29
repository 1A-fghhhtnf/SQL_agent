from dataclasses import dataclass
from pathlib import Path

from omegaconf import OmegaConf


@dataclass
class FileConfig:
    enable: bool
    level: str
    path: str
    rotation: str
    retention: str


@dataclass
class ConsoleConfig:
    enable: bool
    level: str

# 数据库配置
@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class QdrantConfig:
    host: str
    port: int
    embedding_size: int


@dataclass
class EmbeddingConfig:
    host: str
    port: int
    model: str

@dataclass
class LLMConfig:
    model_name: str
    api_key: str
    base_url: str


@dataclass
class ESConfig:
    host: str
    port: int
    index_name: str

@dataclass
class LoggingConfig:
    file: FileConfig
    console: ConsoleConfig


@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta: DBConfig
    db_dw: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: ESConfig
    llm: LLMConfig

# 1.从yaml文件读取应用配置信息得到OmegaConf对象 包含所有内容
app_config_path = Path(__file__).parents[2] / 'conf' / 'app_config.yaml'
content = OmegaConf.load(app_config_path)

# 2.从dataclass对象中得到OmegaConf对象  包含结构
structured = OmegaConf.structured(AppConfig)

# 3.将内容结构合并后转为DataClass对象  当前模块产生单例对象
app_config: AppConfig = OmegaConf.to_object(OmegaConf.merge(structured, content))
