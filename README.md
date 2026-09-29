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