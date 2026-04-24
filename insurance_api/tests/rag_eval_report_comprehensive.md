# RAG 综合评测报告

## 总览

| 指标 | 数值 |
|---|---:|
| 总样本数 | 100 |
| 成功请求数 | 0 |
| 状态准确率(status_accuracy) | 0.00% |
| 引用命中率(citation_hit_rate) | 0.00% |
| 词面关键词召回(answer_keyword_recall_lexical) | 0.00% |
| 语义关键词召回(answer_keyword_recall_semantic) | 0.00% |
| 证据精确率(evidence_precision) | 0.00% |
| 证据召回率(evidence_recall) | 0.00% |
| 拒答率(refusal_rate) | 0.00% |
| 误拒答率(false_refusal_rate) | 0.00% |
| 平均时延(avg_latency_ms) | 0.00 |
| P95 时延(p95_latency_ms) | 0.00 |
| 质量分(quality_score) | 0.00% |
| 归因分(grounding_score) | 0.00% |
| 性能分(performance_score) | 100.00% |
| 综合分(overall_score) | 15.00% |

## 明细

### Case 1

- 名称: 告知义务拒赔-001
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本001，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 2

- 名称: 告知义务拒赔-002
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本002，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 3

- 名称: 告知义务拒赔-003
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本003，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 4

- 名称: 告知义务拒赔-004
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本004，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 5

- 名称: 告知义务拒赔-005
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本005，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 6

- 名称: 告知义务拒赔-006
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本006，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 7

- 名称: 告知义务拒赔-007
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本007，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 8

- 名称: 告知义务拒赔-008
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本008，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 9

- 名称: 告知义务拒赔-009
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本009，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 10

- 名称: 告知义务拒赔-010
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本010，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 11

- 名称: 告知义务拒赔-011
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本011，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 12

- 名称: 告知义务拒赔-012
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本012，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 13

- 名称: 告知义务拒赔-013
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本013，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 14

- 名称: 告知义务拒赔-014
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本014，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 15

- 名称: 告知义务拒赔-015
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本015，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 16

- 名称: 告知义务拒赔-016
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本016，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 17

- 名称: 告知义务拒赔-017
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本017，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 18

- 名称: 告知义务拒赔-018
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本018，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 19

- 名称: 告知义务拒赔-019
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本019，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 20

- 名称: 告知义务拒赔-020
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本020，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 21

- 名称: 告知义务拒赔-021
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本021，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 22

- 名称: 告知义务拒赔-022
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本022，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 23

- 名称: 告知义务拒赔-023
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本023，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 24

- 名称: 告知义务拒赔-024
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本024，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 25

- 名称: 告知义务拒赔-025
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本025，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 26

- 名称: 告知义务拒赔-026
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本026，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 27

- 名称: 告知义务拒赔-027
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本027，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 28

- 名称: 告知义务拒赔-028
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本028，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 29

- 名称: 告知义务拒赔-029
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本029，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 30

- 名称: 告知义务拒赔-030
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本030，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 31

- 名称: 告知义务拒赔-031
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本031，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 32

- 名称: 告知义务拒赔-032
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本032，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 33

- 名称: 告知义务拒赔-033
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本033，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 34

- 名称: 告知义务拒赔-034
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本034，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 35

- 名称: 告知义务拒赔-035
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本035，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 36

- 名称: 告知义务拒赔-036
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本036，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 37

- 名称: 告知义务拒赔-037
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本037，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 38

- 名称: 告知义务拒赔-038
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本038，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 39

- 名称: 告知义务拒赔-039
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本039，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 40

- 名称: 告知义务拒赔-040
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本040，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 41

- 名称: 告知义务拒赔-041
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本041，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 42

- 名称: 告知义务拒赔-042
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本042，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 43

- 名称: 告知义务拒赔-043
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本043，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 44

- 名称: 告知义务拒赔-044
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本044，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 45

- 名称: 告知义务拒赔-045
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本045，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 46

- 名称: 告知义务拒赔-046
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本046，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 47

- 名称: 告知义务拒赔-047
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本047，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 48

- 名称: 告知义务拒赔-048
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本048，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 49

- 名称: 告知义务拒赔-049
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本049，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 50

- 名称: 告知义务拒赔-050
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本050，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 51

- 名称: 告知义务拒赔-051
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本051，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 52

- 名称: 告知义务拒赔-052
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本052，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 53

- 名称: 告知义务拒赔-053
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本053，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 54

- 名称: 告知义务拒赔-054
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本054，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 55

- 名称: 告知义务拒赔-055
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本055，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 56

- 名称: 告知义务拒赔-056
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本056，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 57

- 名称: 告知义务拒赔-057
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本057，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 58

- 名称: 告知义务拒赔-058
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本058，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 59

- 名称: 告知义务拒赔-059
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本059，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 60

- 名称: 告知义务拒赔-060
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本060，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 61

- 名称: 告知义务拒赔-061
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本061，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 62

- 名称: 告知义务拒赔-062
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本062，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 63

- 名称: 告知义务拒赔-063
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本063，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 64

- 名称: 告知义务拒赔-064
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本064，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 65

- 名称: 告知义务拒赔-065
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本065，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 66

- 名称: 告知义务拒赔-066
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本066，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 67

- 名称: 告知义务拒赔-067
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本067，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 68

- 名称: 告知义务拒赔-068
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本068，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 69

- 名称: 告知义务拒赔-069
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本069，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 70

- 名称: 告知义务拒赔-070
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本070，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 71

- 名称: 告知义务拒赔-071
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本071，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 72

- 名称: 告知义务拒赔-072
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本072，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 73

- 名称: 告知义务拒赔-073
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本073，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 74

- 名称: 告知义务拒赔-074
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本074，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 75

- 名称: 告知义务拒赔-075
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本075，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 76

- 名称: 告知义务拒赔-076
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本076，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 77

- 名称: 告知义务拒赔-077
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本077，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 78

- 名称: 告知义务拒赔-078
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本078，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 79

- 名称: 告知义务拒赔-079
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本079，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 80

- 名称: 告知义务拒赔-080
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本080，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 81

- 名称: 告知义务拒赔-081
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本081，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 82

- 名称: 告知义务拒赔-082
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本082，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 83

- 名称: 告知义务拒赔-083
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本083，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 84

- 名称: 告知义务拒赔-084
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本084，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 85

- 名称: 告知义务拒赔-085
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本085，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 86

- 名称: 告知义务拒赔-086
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本086，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 87

- 名称: 告知义务拒赔-087
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本087，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 88

- 名称: 告知义务拒赔-088
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本088，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 89

- 名称: 告知义务拒赔-089
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本089，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 90

- 名称: 告知义务拒赔-090
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本090，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 91

- 名称: 告知义务拒赔-091
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本091，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 92

- 名称: 告知义务拒赔-092
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本092，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 93

- 名称: 告知义务拒赔-093
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本093，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 94

- 名称: 告知义务拒赔-094
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本094，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 95

- 名称: 告知义务拒赔-095
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本095，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 96

- 名称: 告知义务拒赔-096
- 文档: test_contract.pdf
- 问题: 若投保时未如实告知既往病史，是否会影响理赔结果？（样本096，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 97

- 名称: 告知义务拒赔-097
- 文档: test_contract.pdf
- 问题: 投保人没有履行如实告知义务，保险公司可否拒赔？（样本097，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 98

- 名称: 告知义务拒赔-098
- 文档: test_contract.pdf
- 问题: 请说明未如实告知健康情况时的理赔责任判断。（样本098，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 99

- 名称: 告知义务拒赔-099
- 文档: test_contract.pdf
- 问题: 在如实告知条款下，未告知病史会造成什么理赔后果？（样本099，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused

### Case 100

- 名称: 告知义务拒赔-100
- 文档: test_contract.pdf
- 问题: 依据合同，隐瞒既往病史是否可能触发拒赔？（样本100，主题:告知义务拒赔）
- 执行成功: False
- 错误: [Errno 111] Connection refused
