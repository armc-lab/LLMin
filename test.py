# python test.py
import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from PyPDF2 import PdfReader

# 模型路径
model_path = "/data2/wangliangmin/snap/Baichuan"
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True
)
model.eval()

# 读取并提取保险合同核心内容
def extract_core_content(text):
    key_terms = ["健康告知", "如实告知", "免责", "不保", "除外责任", "投保范围", "等待期"]
    lines = text.splitlines()
    selected = [line for line in lines if any(term in line for term in key_terms)]
    return "\n".join(selected[:100])  # 限制最多100行防止超长

# 文件读取与核心提取
def read_and_extract(file):
    if file.name.endswith(".txt"):
        with open(file.name, 'r', encoding='utf-8') as f:
            content = f.read()
    elif file.name.endswith(".pdf"):
        pdf = PdfReader(file.name)
        content = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    else:
        return "暂不支持该文件格式。", ""

    core_info = extract_core_content(content)
    return content, core_info

# 主问答函数
def insurance_qa(user_question, file):
    if file is None:
        return "请先上传一个 PDF 或 TXT 格式的保险合同。"

    full_text, core_summary = read_and_extract(file)

    prompt = f"""
你是一个精通保险条款、善于通俗解释的智能助手，任务是根据用户上传的保险合同条款内容，
结合健康告知、免责条款和投保要求，判断用户是否符合条件，是否可以理赔。

【合同摘要】
{core_summary}

【用户问题】
{user_question}

【请按以下结构输出】
1. 是否可以投保？
2. 是否影响理赔？
3. 是否需要特别健康告知？
4. 引用合同条款中的关键内容作为解释依据。
请回答尽可能通俗易懂，专业且具体：
""".strip()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=tokenizer.model_max_length).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            do_sample=False,  # 关闭随机采样，提升稳定性
            repetition_penalty=1.1,
            eos_token_id=tokenizer.eos_token_id
        )

    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    answer = full_output[len(prompt):].strip() if full_output.startswith(prompt) else full_output.strip()

    torch.cuda.empty_cache()
    return answer

# Gradio界面
gr.Interface(
    fn=insurance_qa,
    inputs=[
        gr.Textbox(label="请输入你的问题", placeholder="如：我有高血压，可以投这份保险吗？", lines=2),
        gr.File(label="上传 PDF 或 TXT 格式的保险合同", file_types=[".pdf", ".txt"])
    ],
    outputs=gr.Textbox(label="大模型通俗化回答", lines=10),
    title="保险合同通俗化解释助手",
    description="上传合同并提出具体问题（如既往病史、健康告知、理赔范围），系统将引用条款内容做出专业判断。",
    allow_flagging="never"
    ).launch(share=True, server_port=8080, server_name="0.0.0.0")

