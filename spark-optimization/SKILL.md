---
name: spark-optimization
description: "Apache Spark 作业优化：分区策略、缓存、shuffle 优化和内存调优。用于提升 Spark 性能、调试慢作业或扩展数据处理管道。触发词：Spark、性能优化、分区、缓存、shuffle、数据倾斜。"
---

# Apache Spark Optimization

生产级 Apache Spark 作业优化模式，包括分区策略、内存管理、shuffle 优化和性能调优。

## 何时使用此 Skill

- 优化慢的 Spark 作业
- 调优内存和执行器配置
- 实现高效分区策略
- 调试 Spark 性能问题
- 为大数据集扩展 Spark 管道
- 减少 shuffle 和数据倾斜

## 核心概念

### 1. Spark 执行模型

```
Driver Program
    ↓
Job（由 action 触发）
    ↓
Stages（由 shuffle 分隔）
    ↓
Tasks（每个分区一个）
```

### 2. 关键性能因素

| 因素 | 影响 | 解决方案 |
|------|------|----------|
| **Shuffle** | 网络 I/O、磁盘 I/O | 最小化宽转换 |
| **数据倾斜** | 任务时长不均 | 加盐、广播连接 |
| **序列化** | CPU 开销 | 使用 Kryo、列式格式 |
| **内存** | GC 压力、数据溢出 | 调优执行器内存 |
| **分区** | 并行度 | 合理设置分区大小 |

## 快速开始

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# 创建优化的 Spark session
spark = (SparkSession.builder
    .appName("OptimizedJob")
    .config("spark.sql.adaptive.enabled", "true")
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
    .config("spark.sql.adaptive.skewJoin.enabled", "true")
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
    .config("spark.sql.shuffle.partitions", "200")
    .getOrCreate())

# 使用优化设置读取
df = (spark.read
    .format("parquet")
    .option("mergeSchema", "false")
    .load("s3://bucket/data/"))

# 高效转换
result = (df
    .filter(F.col("date") >= "2024-01-01")
    .select("id", "amount", "category")
    .groupBy("category")
    .agg(F.sum("amount").alias("total")))

result.write.mode("overwrite").parquet("s3://bucket/output/")
```

## 模式

### 模式 1: 最优分区

```python
# 计算最优分区数
def calculate_partitions(data_size_gb: float, partition_size_mb: int = 128) -> int:
    """最优分区大小：128MB - 256MB"""
    return max(int(data_size_gb * 1024 / partition_size_mb), 1)

# 重新分区以实现均匀分布
df_repartitioned = df.repartition(200, "partition_key")

# 合并以减少分区（无 shuffle）
df_coalesced = df.coalesce(100)
```

### 模式 2: 连接优化

```python
# 1. 广播连接 - 小表连接
# 最佳条件：一侧 < 10MB
small_df = spark.read.parquet("s3://bucket/small_table/")  # < 10MB
large_df = spark.read.parquet("s3://bucket/large_table/")  # TBs

# 显式广播提示
result = large_df.join(
    F.broadcast(small_df),
    on="key",
    how="left"
)

# 2. 排序合并连接 - 大表的默认选择
result = large_df1.join(large_df2, on="key", how="inner")

# 3. 桶连接 - 预排序，连接时无 shuffle
(df.write
    .bucketBy(200, "customer_id")
    .sortBy("customer_id")
    .mode("overwrite")
    .saveAsTable("bucketed_orders"))

# 4. 倾斜连接处理
# 启用 AQE 倾斜连接优化
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")
```

### 模式 3: 缓存和持久化

```python
from pyspark import StorageLevel

# 缓存重用 DataFrame
df = spark.read.parquet("s3://bucket/data/")
df_filtered = df.filter(F.col("status") == "active")

# 在内存中缓存（默认 MEMORY_AND_DISK）
df_filtered.cache()

# 强制物化
df_filtered.count()

# 存储级别说明：
# MEMORY_ONLY - 快，但可能放不下
# MEMORY_AND_DISK - 溢出到磁盘（推荐）
# MEMORY_ONLY_SER - 序列化，占用内存少，CPU 多
# DISK_ONLY - 内存紧张时
```

### 模式 4: 内存调优

```python
# 执行器内存配置
# spark-submit --executor-memory 8g --executor-cores 4

# 内存分解（8GB 执行器）：
# - spark.memory.fraction = 0.6（60% = 4.8GB 用于执行 + 存储）
#   - spark.memory.storageFraction = 0.5
# - 40% = 3.2GB 用于用户数据结构和内部元数据

spark = (SparkSession.builder
    .config("spark.executor.memory", "8g")
    .config("spark.executor.memoryOverhead", "2g")
    .config("spark.memory.fraction", "0.6")
    .config("spark.memory.storageFraction", "0.5")
    .getOrCreate())
```

### 模式 5: Shuffle 优化

```python
# 减少 shuffle 数据大小
spark.conf.set("spark.sql.shuffle.partitions", "auto")  # 配合 AQE
spark.conf.set("spark.shuffle.compress", "true")

# Shuffle 前预聚合
df_optimized = (df
    .groupBy("key", "partition_col")
    .agg(F.sum("value").alias("partial_sum"))
    .groupBy("key")
    .agg(F.sum("partial_sum").alias("total")))
```

### 模式 6: 数据格式优化

```python
# Parquet 优化
(df.write
    .option("compression", "snappy")
    .option("parquet.block.size", 128 * 1024 * 1024)
    .parquet("s3://bucket/output/"))

# Delta Lake 优化
(df.write
    .format("delta")
    .option("optimizeWrite", "true")
    .option("autoCompact", "true")
    .mode("overwrite")
    .save("s3://bucket/delta_table/"))
```

### 模式 7: 监控和调试

```python
# 启用详细指标
spark.conf.set("spark.sql.codegen.wholeStage", "true")

# 解释查询计划
df.explain(mode="extended")

# 识别数据倾斜
def check_partition_skew(df):
    partition_counts = (df
        .withColumn("partition_id", F.spark_partition_id())
        .groupBy("partition_id")
        .count()
        .orderBy(F.desc("count")))
    skew_ratio = stats["max"] / stats["avg"]
    print(f"Skew ratio: {skew_ratio:.2f}x (>2x indicates skew)")
```

## 配置速查表

```python
# 生产配置模板
spark_configs = {
    # 自适应查询执行（AQE）
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.adaptive.skewJoin.enabled": "true",

    # 内存
    "spark.executor.memory": "8g",
    "spark.memory.fraction": "0.6",
    "spark.memory.storageFraction": "0.5",

    # 并行度
    "spark.sql.shuffle.partitions": "200",

    # 序列化
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer",

    # 广播
    "spark.sql.autoBroadcastJoinThreshold": "50MB",
}
```

## 最佳实践

### 应该做

- **启用 AQE** - 自适应查询执行处理许多问题
- **使用 Parquet/Delta** - 带压缩的列式格式
- **广播小表** - 避免小连接的 shuffle
- **监控 Spark UI** - 检查倾斜、溢出、GC
- **正确设置分区** - 每个分区 128MB - 256MB

### 不应该做

- **不收集大数据** - 保持数据分布式
- **不必要地使用 UDF** - 使用内置函数
- **不过度缓存** - 内存有限
- **不忽略数据倾斜** - 它主导作业时间
- **不用 `.count()` 判断存在** - 使用 `.take(1)` 或 `.isEmpty()`
