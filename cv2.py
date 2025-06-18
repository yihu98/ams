import streamlit as st
from google import genai
from google.genai import types

st.title("简历优化")

# API Key input in sidebar
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")
    "[Get a Gemini API key](https://aistudio.google.com/app/apikey)"

# Main content
job_title = st.text_input("请输入目标职位")

resume_sections = ["基本信息", "教育经历", "工作经历", "项目经历", "专业能力", "自我总结"]
selected_section = st.selectbox("请选择简历模块", resume_sections)

resume_content = st.text_area("请输入简历内容", height=200)

if st.button("优化简历"):
    if not api_key:
        st.error("请先输入 Gemini API Key")
        st.stop()
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""你是一位专业的简历优化顾问，擅长根据特定职位需求来优化求职者的简历内容。你的任务是根据给定的职位和简历部分，对简历内容进行优化和改进。请仔细阅读以下信息，并按照指示进行操作。

职位名称：
<job_title>
{job_title}
</job_title>

简历部分：
<resume_section>
{selected_section}
</resume_section>

原始简历内容：
<resume_content>
{resume_content}
</resume_content>

请按照以下步骤优化简历内容：

1. 分析职位和简历：
   - 仔细分析职位名称和简历部分，确定这个职位可能需要的关键技能和经验。
   - 审查原始简历内容，找出与职位相关的重要信息。

2. 优化思路：
   - 列出与职位最相关的经验和技能。
   - 思考原文本中需要优化的地方，并展开进行说明。
   - 考虑如何编造具体的数字和成就来量化成果，增加简历的说服力。
   - 检查并纠正任何语法或拼写错误。
   - 考虑使用STAR法则（情境、任务、行动、结果）来优化简历内容。

3. 修改简历：
   - 根据上述思考和优化点对简历内容进行修改。
   - 使用简洁、专业的语言，避免冗长或不必要的内容。
   - 加入与职位相关的关键词。
   - 使用第三人称来表述，并且输出的内容跟原文本段落格式和风格和字数一致。

请将你的回答按以下格式输出：

<analysis>
在这里写下你对职位要求和原始简历内容的分析。
</analysis>

<optimization_ideas>
在这里列出你的优化思路和建议。
</optimization_ideas>

<optimized_content>
在这里写下优化后的简历内容。
</optimized_content>"""

    try:
        model = "gemini-2.5-pro-preview-06-05"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            thinking_config = types.ThinkingConfig(
                thinking_budget=-1,
            ),
            response_mime_type="text/plain",
        )

        response_chunks = []
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response_chunks.append(chunk.text)
        
        response = "".join(response_chunks)
        
        # Extract sections using string manipulation
        analysis = response[response.find("<analysis>")+10:response.find("</analysis>")].strip()
        optimization = response[response.find("<optimization_ideas>")+19:response.find("</optimization_ideas>")].strip()
        optimized = response[response.find("<optimized_content>")+18:response.find("</optimized_content>")].strip()
        
        # Display results in expandable sections
        with st.expander("🔍分析", expanded=True):
            st.write(analysis)
        with st.expander("🤔优化建议", expanded=True):
            st.write(optimization)
        with st.expander("✨️优化后的内容", expanded=True):
            st.write(optimized)
            
    except Exception as e:
        st.error(f"发生错误: {str(e)}")
