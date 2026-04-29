# RAG 指标测试说明

本文档说明如何对本项目 RAG 问答效果进行量化测试。

## 1. 测试目标

通过固定测试集评估以下维度：

1. 检索命中质量（是否返回命中状态）
2. 引用片段命中质量（`citations` 是否包含关键依据）
3. 回答覆盖质量（回答是否覆盖期望关键词）
4. 性能时延（平均/P95）

## 2. 测试脚本与样例

- 评测脚本: [scripts/evaluate_rag.py](scripts/evaluate_rag.py)
- 样例测试集: [tests/rag_eval_cases.sample.json](tests/rag_eval_cases.sample.json)

样例字段说明：

- `document_path`: 测试文档路径（相对项目根目录）
- `question`: 用户问题
- `expected.status`: 期望命中状态（常见为 `hit`）
- `expected.citation_keywords`: 期望在引用中出现的关键词
- `expected.answer_keywords`: 期望在回答中覆盖的关键词

## 3. 执行步骤

### 3.1 启动 API

先启动服务：

```bash
python main_api.py
```

默认监听 `http://127.0.0.1:8001`。

### 3.2 运行评测

```bash
python scripts/evaluate_rag.py \
  --cases tests/rag_eval_cases.sample.json \
  --base-url http://127.0.0.1:8001
```

可选参数：

- `--output-json`：明细 JSON 输出路径（默认 `tests/rag_eval_result.json`）
- `--output-md`：Markdown 报告输出路径（默认 `tests/rag_eval_report.md`）

## 4. 指标定义

设成功请求集合为 $S$，其大小为 $|S|$。

1. `status_accuracy`

$$
\text{status\_accuracy} = \frac{\#(\text{pred\_status} = \text{expected\_status})}{|S|}
$$

2. `citation_hit_rate`

$$
\text{citation\_hit\_rate} = \frac{\#(\text{citations 包含任一期望关键词})}{|S|}
$$

3. `answer_keyword_recall`

对每个样本，记回答命中的关键词比例为 $r_i$：

$$
r_i = \frac{\#(\text{answer\_keywords 在回答中被命中})}{\#(\text{answer\_keywords})}
$$

总体：

$$
\text{answer\_keyword\_recall} = \frac{1}{|S|}\sum_{i \in S} r_i
$$

4. 时延指标

- `avg_latency_ms`: 平均响应时延
- `p95_latency_ms`: 95 分位响应时延

## 5. 输出文件

1. 结果明细 JSON: [tests/rag_eval_result.json](tests/rag_eval_result.json)
2. 可读报告 Markdown: [tests/rag_eval_report.md](tests/rag_eval_report.md)

说明：上述两份文件在首次执行脚本后生成。

## 6. 建议验收阈值（可按业务调整）

1. `status_accuracy >= 0.90`
2. `citation_hit_rate >= 0.85`
3. `answer_keyword_recall >= 0.80`
4. `p95_latency_ms` 在当前机器资源下稳定（建议记录基线）

## 7. 常见问题

1. 全部样本失败：优先检查 vLLM 服务是否启动、端口是否可访问。
2. 指标波动大：检查模型温度、测试文档版本、硬件负载是否变化。
3. 引用命中低：优先排查分块质量、检索阈值、规则优先关键字配置。

## 8. 综合评测脚本（推荐）

当你需要更完整地衡量 RAG 质量时，建议使用：

- [scripts/evaluate_rag_comprehensive.py](scripts/evaluate_rag_comprehensive.py)

执行示例：

```bash
python scripts/evaluate_rag_comprehensive.py \
  --cases tests/rag_eval_cases.100.json \
  --base-url http://127.0.0.1:8001
```

默认输出：

1. `tests/rag_eval_result_comprehensive.json`
2. `tests/rag_eval_report_comprehensive.md`

新增关键指标：

1. `answer_keyword_recall_semantic`：语义关键词召回（支持同义词组）。
2. `evidence_precision`：证据精确率（命中关键词的引用占比）。
3. `evidence_recall`：证据召回率（被引用覆盖的证据关键词占比）。
4. `refusal_rate` / `false_refusal_rate`：拒答率与误拒答率。
5. `quality_score` / `grounding_score` / `performance_score` / `overall_score`：分维度与综合分。

测试集可选新增字段：

1. `expected.answer_keyword_groups`：二维数组，每组为同义词集合。
2. `expected.should_refuse`：该样本是否期望拒答（默认 false）。

示例：

```json
{
  "expected": {
    "status": "hit",
    "citation_keywords": ["11.6", "如实告知"],
    "answer_keywords": ["如实告知", "拒赔", "条款"],
    "answer_keyword_groups": [
      ["拒赔", "不承担保险责任"],
      ["条款", "第11.6条", "合同依据"]
    ],
    "should_refuse": false
  }
}
```
