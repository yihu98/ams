import streamlit as st
import anthropic

with st.sidebar:
    anthropic_api_key = st.text_input("Anthropic API Key", key="translator_api_key", type="password")

st.title("🌐 中英文翻译助手")

chinese_text = st.text_area(
    "请输入要翻译的中文",
    placeholder="在这里输入中文文本...",
    height=150
)

context_text = st.text_area(
    "补充说明（选填）",
    placeholder="在这里输入额外的上下文信息,以帮助更准确的翻译...",
    height=100
)

if chinese_text and not anthropic_api_key:
    st.info("请先输入您的 Anthropic API Key 以继续使用")

if st.button("翻译") and chinese_text and anthropic_api_key:
    prompt = f"""You are a professional translator specializing in software localization. Your task is to translate Chinese user interface text into three potential English translations. These translations should be suitable for use in software interfaces and reflect natural language usage in English-speaking countries.

Here is the Chinese text to translate:
<chinese_text>
{chinese_text}
</chinese_text>

Additional context information:
{context_text if context_text else "No additional context provided."}

Please provide three different English translations for this text. Each translation should:
1. Accurately convey the meaning of the original Chinese text
2. Be appropriate for use in a software user interface
3. Sound natural and idiomatic to native English speakers

Format your response as follows:
<translation1>First English translation</translation1>
<translation2>Second English translation</translation2>
<translation3>Third English translation</translation3>

There is no need for any note.

Guidelines for high-quality translations:
- Ensure that each translation is distinct and offers a unique way of expressing the concept
- Consider the context of software UI when translating (e.g., conciseness, clarity)
- Avoid literal translations that may sound awkward in English
- Use standard capitalization and punctuation appropriate for UI text

Remember, these translations will be used in a software interface, so they should be clear, concise, and user-friendly. Avoid overly technical language unless it's necessary for accuracy.

Provide your three translations now, each wrapped in the appropriate XML tags as shown above.

Here are some example：
<examples>
<example>
<CHINESE_TEXT>
标准会员
</CHINESE_TEXT>
<ideal_output>
<translation1>Standard Member</translation1>
<translation2>Regular Membership</translation2>
<translation3>Basic Member</translation3>
</ideal_output>
</example>
<example>
<CHINESE_TEXT>
注册
</CHINESE_TEXT>
<ideal_output>
<translation1>Sign Up</translation1>
<translation2>Register</translation2>
<translation3>Create Account</translation3>
</ideal_output>
</example>

"""

    client = anthropic.Client(api_key=anthropic_api_key)
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
    
    st.write("### 翻译结果")
    text = response.content[0].text
    
    import re
    versions = []
    for i in range(1, 4):
        pattern = f"<translation{i}>(.*?)</translation{i}>"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            versions.append(match.group(1).strip())
    
    for i, translation in enumerate(versions, 1):
        st.write(f"**版本 {i}:**")
        st.text(translation)
        if st.button(f"复制版本 {i}", key=f"copy_btn_{i}"):
            st.write(f"已复制版本 {i}")
        st.divider()
