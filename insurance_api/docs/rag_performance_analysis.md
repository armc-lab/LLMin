# RAG 性能分析报告

## 1. 实验概况

1. 日期：2026-03-18。
2. 代码基线：当前 main_api.py（已加入语义+词法融合排序与关键词中心化引用片段）。
3. 样本集：tests/rag_eval_cases.sample.json（10 条）。
4. 执行命令：

```bash
python scripts/evaluate_rag.py --cases tests/rag_eval_cases.sample.json --base-url http://127.0.0.1:8001
```

5. 输出文件：
- tests/rag_eval_result.json
- tests/rag_eval_report.md

## 2. 核心指标

本次实测指标：

1. total = 10
2. success = 10
3. status_accuracy = 1.00
4. citation_hit_rate = 0.90
5. answer_keyword_recall = 0.70
6. avg_latency_ms = 7332.62
7. p95_latency_ms = 35354.13

## 3. 结果解读

### 3.1 质量维度

1. 状态判定稳定：status_accuracy 达到 100%。
2. 引用可解释性较好：citation_hit_rate 达到 90%。
3. 回答覆盖仍有提升空间：answer_keyword_recall 为 70%。

### 3.2 性能维度

1. 平均时延约 7.3s，可用于低并发问答场景。
2. P95 达到 35.35s，尾延迟较高，存在抖动风险。
3. Case 1 出现 35s 级耗时，可能受模型生成长度或 GPU 瞬时负载影响。

## 4. 典型问题样本

1. Case 10（保险金申请对应哪个条款）出现 citation_ok=False。
2. 部分样本回答有泛化描述，关键词覆盖不足，导致 answer_keyword_recall 偏低。
3. 从报告预览看，个别回答仍会跳到“建议咨询律师”等泛化措辞，说明生成阶段约束仍可加强。

## 5. 原因分析

1. 检索阶段虽然提升了召回，但 top context 中仍可能混入相邻条款，影响模型聚焦。
2. 提示词对“必须回答条款号/章节号”的约束还不够硬。
3. 后处理主要做清洗和结构化，尚未做“答案关键词覆盖校正”。
4. 尾延迟与模型端推理耗时直接相关，且受实时负载影响较大。

## 6. 优化建议（按优先级）

1. 强化答案格式约束：要求结论首句必须包含条款号或章节号；未命中时必须显式写“未检索到原文”。
2. 增加检索重排：在融合分数后增加二次 rerank（可先用轻量规则 rerank）。
3. 引用筛选规则：优先包含问题关键词和条款号的片段，避免泛化上下文进入前 4 条引用。
4. 延迟优化：控制 max_tokens、减少二次调用次数，或给 recommendations 加缓存策略。
5. 回归机制：固定 10 条样本作为每日回归基线，增加按场景分桶统计（告知义务、报案通知、疾病释义、给付规则）。

## 7. 结论

当前 RAG 已具备可用性和较好的可解释性基础（status 与 citation 指标较优），主要短板集中在回答覆盖率与尾延迟。下一阶段建议优先攻关 answer_keyword_recall 和 p95_latency_ms，以提升稳定生产可用性。
