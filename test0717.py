import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_name = "/media/dell/a66902c2-24ef-4948-917a-da97b34531f9/shens/Baichuan"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True
)
model.eval()

def qa_fn(user_question):
    prompt = (
        "请你作为一个专业助手，简洁回答以下问题，不要重复问题内容。\n\n"
        f"问题：{user_question}\n"
        "回答："
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=128,
            do_sample=True,
            top_p=0.9,
            temperature=0.7,
            eos_token_id=tokenizer.eos_token_id
        )
    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)

    print("==== 完整模型输出 ====")
    print(full_output)
    print("==== End ====")

    if full_output.startswith(prompt):
        answer = full_output[len(prompt):].strip()
    else:
        answer = full_output.strip()

    del inputs, outputs
    torch.cuda.empty_cache()

    return answer


gr.Interface(
    fn=qa_fn,
    inputs=gr.Textbox(label="请输入你的问题"),
    outputs=gr.Textbox(label="模型回答"),
    title="大模型问答测试",
    description="输入任何问题，大模型将尝试回答你。"
).launch(share=True)
