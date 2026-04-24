# RAG 测试教程

本文档用于指导在本项目中执行 RAG 效果测试，包含环境准备、服务启动、评测执行与结果解读。

## 1. 前置条件

1. 已安装并可用 conda。
2. 已存在环境 baichuan-chat。
3. 项目目录为 /data2/wangliangmin/snap/Baichuan/insurance_api。
4. 测试合同文件存在：
- test_contract.pdf
- test_contract2.pdf

## 2. 测试文件说明

1. 测试样本集：tests/rag_eval_cases.sample.json。
2. 评测脚本：scripts/evaluate_rag.py。
3. 评测结果输出：
- tests/rag_eval_result.json
- tests/rag_eval_report.md

## 3. 启动顺序（必须）

必须先启动 vLLM，再启动 main_api，最后执行评测脚本。

## 4. 步骤一：启动 vLLM 服务

在终端 A 执行：

```bash
cd /data2/wangliangmin/snap/Baichuan/insurance_api
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate baichuan-chat
bash vllm_runner_fixed.sh
```

健康检查（另开终端）：

```bash
curl http://127.0.0.1:8000/v1/models
```

返回 200 且含模型列表表示成功。

## 5. 步骤二：启动主 API

在终端 B 执行：

```bash
cd /data2/wangliangmin/snap/Baichuan/insurance_api
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate baichuan-chat
python main_api.py
```

健康检查（另开终端）：

```bash
curl http://127.0.0.1:8001/
```

返回 200 表示成功。

## 6. 步骤三：执行评测

在终端 C 执行：

```bash
cd /data2/wangliangmin/snap/Baichuan/insurance_api
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate baichuan-chat
python scripts/evaluate_rag.py --cases tests/rag_eval_cases.sample.json --base-url http://127.0.0.1:8001
```

## 7. 指标说明

1. status_accuracy：状态命中准确率。
2. citation_hit_rate：引用片段命中率。
3. answer_keyword_recall：回答关键词召回率。
4. avg_latency_ms：平均时延。
5. p95_latency_ms：95 分位时延。

## 8. 快速排障

1. 全部样本失败：先检查 8000 和 8001 端口是否可访问。
2. 出现 503：通常是 vLLM 未启动或不可达。
3. 评测脚本报连接失败：确认 main_api 正在运行。
4. 时延过高：检查 GPU 负载、vLLM 并发、模型初始化状态。

## 9. 建议验收阈值

1. status_accuracy >= 0.95。
2. citation_hit_rate >= 0.85。
3. answer_keyword_recall >= 0.75。
4. p95_latency_ms 根据硬件负载设定基线并持续跟踪。
