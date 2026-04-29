# 网络合同爬取脚本

脚本位置：
- `scripts/crawl_contracts_from_web.py`

功能：
- 从种子 URL 开始递归抓取网页链接
- 默认尊重 robots.txt
- 抽取 HTML/PDF 文本
- 按“合同相关关键词”筛选并切块
- 输出 JSONL，可直接用于检索/评测/微调

## 1) 最小示例

```bash
cd /data2/wangliangmin/snap/Baichuan/insurance_api
conda run -n baichuan-chat python scripts/crawl_contracts_from_web.py \
  --seed https://example.com/contracts/ \
  --allow-domain example.com \
  --output-jsonl data/web_contract_chunks.jsonl
```

## 2) 多个种子 URL

先准备 `seeds.txt`（每行一个 URL），例如：

```text
https://example.com/contracts/
https://insurance.example.org/policy/
```

运行：

```bash
cd /data2/wangliangmin/snap/Baichuan/insurance_api
conda run -n baichuan-chat python scripts/crawl_contracts_from_web.py \
  --seeds-file seeds.txt \
  --allow-domain example.com \
  --allow-domain insurance.example.org \
  --max-pages 500 \
  --max-depth 3 \
  --output-jsonl data/web_contract_chunks.jsonl
```

## 3) 常用参数

- `--max-pages`：最大抓取页面数
- `--max-depth`：链接递归深度
- `--delay`：请求间隔（秒）
- `--keyword`：额外关键词，可重复传
- `--download-dir`：保存原始 HTML/PDF 备份
- `--dedup`：按文本块去重
- `--ignore-robots`：忽略 robots（默认不建议）

## 4) 输出格式

每行一条 JSON，字段包括：
- `source_url`
- `file_type` (`html`/`pdf`)
- `title`
- `sha256`
- `fetched_at`
- `chunk_index` / `chunk_count`
- `char_count`
- `text`

## 5) 合规建议

- 仅抓取公开且允许访问的页面
- 默认遵守 robots.txt，不建议关闭
- 控制 `--delay`，避免高频请求影响目标站点
- 抓取前先确认目标网站条款与适用法律
