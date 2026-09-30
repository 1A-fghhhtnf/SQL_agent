项目git地址：https://gitee.com/lvhonlgong/bj260706-data-agent.git
元数据知识库：
	元数据库:
		1. 表信息  2.字段信息  3.指标信息 4.字段指标关系信息
		其中region_name字段信息部分实例值examples=["华南","华东","西北"]  
	向量数据库
		1.字段信息（名称、描述、别名） 2.指标信息（名称、描述、别名）
	全文索引库
		1.维度表中字段取值建立全文索引，支持全文查询 解决准确生成SQL的where 字段取值
	
用户问题：统计华北地区销售额  数据库中地区表一条真实记录：R004	北京市	华北	  中国
	①分词 拆解+llm扩充得到有意义关键词列表
	②语义相似度检索向量库 得到 回答问题需要字段+指标信息 + 手动补齐主外键 dim_region_id（区域表）,dim_region.region_name,fact_order.order_amount,region_id（订单表外键字段）
	③假设基于上述上下文调用llm生成SQL可能：
		1.select sum(order_amount) 销售额 from fact_order fo inner join dim_region dr on fo.region_id = dr.region_id where region_name = "华北地区";  SQL正确 但查不到数据库
		2.select sum(order_amount) 销售额 from fact_order fo inner join dim_region dr on fo.region_id = dr.region_id where region_name = "华北";   SQL正确且能查询到数据
解决：生成SQL过滤条件准确，需要将维度表中字段取值全量存入到ElasticSearch全文索引库
	例如：地区维度表dim_region表中，province（省份） region_name（区域名称） country（国家）
		 上述三个字段所有取值，为每个字段取值构建ES文档（存入ES一条记录），文档结构如下：
		 {
		   "id":"字段id.华北",
		   "value":"华北",
		   "column_id":"dim_region.region_name"
		 }
		 {
		   "id":"字段id.华南",
		   "value":"华南",
		   "column_id":"dim_region.region_name"
		 }
    执行全文检索，将问题拆分为：华北地区/华北/地区 根据三个关键词确定一个文档：推出dim_region.region_name字段ID，查询meta得到字段信息，将 华北 取值追加到region_name的examples=["华南","华东","西北","华北"]  
	 {
	   "id":"字段id.华北",
	   "value":"华北",
	   "column_id":"dim_region.region_name"
	 }
   提供给llm上下文：问题、可选字段（实例值）、指标，准确生成SQL:
   select sum(order_amount) 销售额 from fact_order fo inner join dim_region dr on fo.region_id = dr.region_id where region_name = "华北";
	 

本地windows端口冲突：
 1. netstat -ano|findstr "8000" 查询指定端口被占用进程ID   LISTENING：被监听占用
		TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING       36168
 2. 查询进程，杀掉进程
	taskkill /f /pid 36168

ElastiSearch/ES:Java语言开发**开源、分布式、RESTful 风格的搜索引擎**，基于Apache Lucene 构建，主打**全文检索、结构化检索、日志分析、数据统计**。
Kibana：用于可视化分析数据
作用：用于存储海量数据，对数据进行分析，提供高效率检索（聚合、排序、分组、统计）
	MySQL：强事务场景 核心业务数据：订单、支付、商品、用户 如果使用MySQL like %左模糊索引失效，引起全表扫描查询性能差，检索效果不好
    MongoDB：非关系型文档型数据库 低值业务单一场景：评论、日志、浏览记录、用户行为
	Redis:内存数据库，用于缓存读多写少业务数据 
	ElasticSearch: 全文检索，站内搜索
核心概述：
	MySQL                   ES
   database(数据库)       index(索引库)
    table(表)            type(类型) 在5.x版本后已弃用，不支持自定义 约定俗成一个索引库下只有一个类型：_doc
    column(字段)          field(字段)
	schema(DDL)          mapping(映射)

基于Apache Lucene（jar）底层，倒排索引：根据关键词找文档ID，通过ID查询记录，通过索引快速定位数据，分为三步
一、分词/分析   原始文本：苹果iPhone18ProMax 1TB 主打色白色   小米18 主打 白色
		苹果           1
        iPhone        1
        ProMax        1
        主打           1 
        主打           2
        主打色         1 
        白色           1   
        白色           2
二、去重 去掉重复词条
        白色           1,2
        主打           1,3
		苹果           1
        iPhone        1
        ProMax        1
三、排序
	    iPhone        1
        ProMax        1
        白色           1,2
        苹果           1
        主打           1,3
搜索过程： 苹果白色，白色苹果  先对搜索内容分词 分为：苹果+白色 再根据分词后关键词查询倒排索引列表 找出 来自于1,2号文档（记录），再根据ID查询完整记录

#操作 索引库（映射信息）
PUT /books
GET /books
# 动态映射，根据保存文档中字段取值生成字段类型，不推荐使用
POST books/_doc
{
  "name": "Snow Crash",
  "author": "Neal Stephenson",
  "release_date": "1992-06-01",
  "page_count": 470
}
# 映射mapping规定索引库中字段数据类型，是否需要索引、分词器，如果未指定指定映射，直接新增文档，每个字段数据类型根据提交值类型决定
字符串类型：
    text: 会对内容进行分词（需要指定分词器）适用于全文检索，缺点不支持聚合（分组）跟排序 例如：电商商品标题、博客标题正文
    keyword:不会分词，适用于精确查询，适用于等值查询排序或聚合（分组），缺点不支持全文查询 例如：电商商品品牌、分类，博主昵称
#映射、推荐使用显示映射，根据业务需求指定每个字段数据类型
#分词器使用ik分词器 ik_smart 分词相对粒度大，ik_max_word:分词粒度更细
GET _analyze
{
  "analyzer" : "ik_max_word",
  "text" : "我是中国人，华为手机"
}

# 需求：商品索引库 id,商品标题、分类、品牌、价格、图
PUT goods
{
    "mappings": {
        "properties": {
            "id":{
                "type": "integer"
            },
            "title":{
                "type": "text",
                "analyzer": "ik_max_word"
            },
            "brand":{
                "type": "keyword"
            },
            "price":{
                "type": "integer"
            },
            "image":{
                "type": "keyword",
                "index": false
            }
        }
    }
}

#操作文档 如果没有指定文档ID，ES会自动生成唯一ID ，属性："_id"
PUT goods/_doc/3
{
  "id": 3,
  "title": "苹果笔记本电脑",
  "brand": "苹果",
  "price": 9700,
  "image":"apple.png"
}

POST /_bulk
{ "index" : { "_index" : "goods" } }
{"title": "华为问界汽车", "brand": "华为问界", "price": 5555500, "image": "wj.png"}
{ "index" : { "_index" : "goods" ,"_id":"1"} }
{"title": "苹果手机IPhone18白色最新款1TB国庆节大促销", "brand": "苹果", "price": 100000, "image": "apple.png"}


get product/_search
#查询
GET goods/_doc/1

#场景：用户通过关键词 采用全文查询  DSL用于ES检索
POST goods/_search
{
    "query": {
        "match": {
          "title": "华为手机"
        }
    }
}

# 用户选择某个品牌过滤
POST goods/_search
{
    "query": {
        "term": {
          "brand": {
            "value": "华为问界"
          }
        }
    }
}

# 通过多条件进行查询 通过bool查询组合多条件 must:内部多条件必须同时满足 should:内部多条件有任意条件满足即可 must_not：内部多个条件去反
# 分页参数：from=(页码-1)*页大小 size=每页显示记录
POST goods/_search
{
    "query": {
        "bool": {
            "must": [
              {
                "match": {
                  "title": "手机华为"
                }
              },
              {
                "range": {
                  "price": {
                    "gte": 7000
                  }
                }
              }
            ]
        }
    },
    "from": 0,
    "size": 10
}









