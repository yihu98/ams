import streamlit as st
import anthropic

st.title("💬 书面语转口语润色助手")

question = st.text_area(
    "客户的问题",
    placeholder="请输入客户的原始问题...",
    height=100
)

formal_text = st.text_area(
    "书面化回答",
    placeholder="请输入需要转换成口语的书面化回答文本...", 
    height=150
)

if st.button("开始润色") and formal_text:
    prompt = f"""你的任务是将一段书面化的中文文本转换成3个口语化的中文逐字口语转录文本，作为候选。这个过程需要你将正式的书面语言转化为更自然、更随意的口头表达方式。

客户的问题是：
<question>
{question}
</question>

以下是需要你转换的书面化中文文本作为问题的回答：

<formal_text>
{formal_text}
</formal_text>

请按照以下步骤进行转换：

1. 仔细阅读原文，理解其主要内容和语气。

2. 将书面化的表达替换成更口语化的表达。例如：
   - 将"因此"改为"所以"或"那么"
   - 将"然而"改为"不过"或"但是"
   - 将"即使"改为"就算"或"哪怕"

3. 添加一些口语中常见的语气词，如"嗯"、"那个"、"就是"等。不要有"呃""额"。

4. 适当增加重复、停顿和自我纠正，以模仿真实对话中的特点。

5. 可以加入一些口语化的语法"错误"，如省略主语、谓语或宾语，使用不完整的句子结构等。

6. 将一些较长的句子拆分成更短的句子，使其更符合口语表达习惯。

7. 使用更简单、更直接的词语替换书面语中的复杂词汇。

8.字数跟输入的文本保持差不多。

请将转换后的口语化文本放在<colloquial_text>标签内。确保转换后的文本听起来自然、随意，就像是有人在进行即兴演讲或日常对话。

例如：
<colloquial_text_1>
第一个候选文本
</colloquial_text_1>
<colloquial_text_2>
第二个候选文本
</colloquial_text_2>
<colloquial_text_3>
第三个候选文本
</colloquial_text_3>

记住，转换的关键是保持原文的基本含义，同时使其听起来更像是口头表达。不要过度修改原文的核心信息，但要让它听起来更自然、更随意。

现在，请开始转换工作，将给定的书面化文本转换为口语化的表达。"""

    try:
        client = anthropic.Client(api_key="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")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        )
        
        st.write("### 口语化润色结果")
        text = response.content[0].text
        
        import re
        versions = []
        for i in range(1, 4):
            pattern = f"<colloquial_text_{i}>(.*?)</colloquial_text_{i}>"
            match = re.search(pattern, text, re.DOTALL)
            if match:
                versions.append(match.group(1).strip())
        
        if not versions:
            st.error("未能正确解析AI返回的结果,请重试")
        else:
            for i, version in enumerate(versions, 1):
                st.write(f"**版本 {i}:**")
                st.text_area(f"版本 {i}", value=version, height=200)
                st.divider()
    except Exception as e:
        st.error(f"发生错误: {str(e)}")
