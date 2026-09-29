from dataclasses import dataclass
from pathlib import Path

from omegaconf import OmegaConf

from app.conf.app_config import app_config

# 需求：读取text_config.yaml文件信息，封装到数据类@dataclass中方便获取参数值
user_config_path = Path(__file__).parents[2] / 'conf' / 'text_config.yaml'
conf = OmegaConf.load(user_config_path)
# omegaconf.dictconfig.DictConfig
print(type(conf))
# 获取配置信息
print(conf)

@dataclass
class UserConfig:
    name: str
    age: int
    height: float

# 2. 将读取到yaml；配置信息封装dataclass数据类对象中
structured = OmegaConf.structured(UserConfig)
# omegaconf.dictconfig.DictConfig
print(type(structured))
print(structured)

# 3. 将两个对象OmegaConf合并
# merge = OmegaConf.merge(structured, conf)
# print(type(merge))
# print(merge)

# 4. 将OmegaConf对象转为dataclass
# to_object:UserConfig = OmegaConf.to_object(merge)
# print(type(to_object))
# print(to_object)

user_config:UserConfig = OmegaConf.to_object(OmegaConf.merge(structured, conf))
print(user_config)

if __name__ == '__main__':
    print(app_config.db_meta)