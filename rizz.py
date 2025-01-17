import streamlit as st
from PIL import Image
import io
import base64
import anthropic
import mimetypes

# 设置固定的 API key
def process_image(uploaded_file):
    """处理上传的图片文件，返回base64编码和MIME类型"""
    try:
        # 读取图片
        image = Image.open(uploaded_file)
        
        # 获取实际的图片格式
        if image.format:
            mime_type = f"image/{image.format.lower()}"
        else:
            mime_type = "image/jpeg"  # 默认使用JPEG
        
        # 转换为RGB模式（如果需要）
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        
        # 压缩图片
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format or 'JPEG', quality=85, optimize=True)
        img_byte_arr.seek(0)
        
        # 检查文件大小
        file_size = len(img_byte_arr.getvalue())
        max_size = 5 * 1024 * 1024  # 5MB
        
        # 如果需要，继续压缩
        if file_size > max_size:
            quality = int((max_size / file_size) * 85)
            quality = max(quality, 30)
            
            while file_size > max_size and quality > 30:
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=image.format or 'JPEG', quality=quality, optimize=True)
                file_size = len(img_byte_arr.getvalue())
                if file_size > max_size:
                    width, height = image.size
                    image = image.resize((int(width*0.9), int(height*0.9)), Image.LANCZOS)
                quality = max(quality - 5, 30)
        
        # 转换为base64
        img_str = base64.b64encode(img_byte_arr.getvalue()).decode()
        
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime_type,
                "data": img_str
            }
        }
        
    except Exception as e:
        raise Exception(f"图片处理失败: {str(e)}")

st.set_page_config(page_title="聊天回复助手", layout="wide")
st.title("回复助手")

with st.sidebar:
    st.markdown("""
    ### API密钥设置
    1. 访问 [Anthropic Console](https://console.anthropic.com/)
    2. 注册并登录账号
    3. 在控制台中创建新的API密钥
    4. 复制API密钥并粘贴到下方输入框
    """)
    anthropic_api_key = st.text_input("Anthropic API Key", key="file_qa_api_key", type="password", help="请输入你的Anthropic API密钥")
    
    st.markdown("""
    ### 使用说明
    1. 上传聊天截图（支持 JPG、PNG 格式）
    2. 点击"生成回复建议"按钮
    3. 等待系统分析并生成建议
    
    **注意**：
    - 图片大小不能超过 5MB
    - 最多可以生成10次回复建议
    """)

if 'suggestions_count' not in st.session_state:
    st.session_state.suggestions_count = 0

if 'all_suggestions' not in st.session_state:
    st.session_state.all_suggestions = []

uploaded_file = st.file_uploader("上传聊天截图", type=["png", "jpg", "jpeg"])

if uploaded_file:
    if st.button("清空历史回复"):
        st.session_state.suggestions_count = 0
        st.session_state.all_suggestions = []
        st.success("历史回复已清空")

    if st.button("生成回复建议", type="primary", disabled=st.session_state.suggestions_count >= 10):
        with st.spinner("正在分析聊天记录，生成建议中..."):
            try:
                # 处理图片
                image_content = process_image(uploaded_file)
                
                # 创建消息内容
                message_content = [
                    image_content,
                    {
                        "type": "text",
                        "text": """你正在帮助某人在与暗恋对象的对话中构思回复。你将获得聊天记录截图，生成三个简短的一句话回复。以下是你的任务：

1. 分析对话，你需要关注：
- 对话的语气和风格；
- 正在讨论的任何特定主题或主题；
- 对方发送的最后一条消息；

2. 根据您的分析，生成三个简短的一句话回复建议：
- 保持对话的当前语气和风格；
- 如果没有很好的话题延展方向，就开启一个新话题；
- 适合与暗恋对象交流（即友好、可能调情，但不要过于直接）；
- 如果对方没有给你emoji表情，那么输出也不要有emoji表情；

3 在三个 <suggestion>  </suggestion> 标签内提供您的回复建议。

请在三个<suggestion></suggestion>标签内提供回复建议。不要包含任何解释或评论。"""
                    }
                ]
                # 调用 API
                if not anthropic_api_key:
                    st.error("请先输入你的Anthropic API密钥")
                    st.stop()
                client = anthropic.Anthropic(api_key=anthropic_api_key)
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    temperature=0.5,
                    messages=[{
                        "role": "user",
                        "content": message_content
                    }]
                )
                
                # 处理结果
                suggestions = message.content[0].text.split("</suggestion>")
                new_suggestions = []
                for suggestion in suggestions[:3]:
                    cleaned_suggestion = suggestion.replace("<suggestion>", "").strip()
                    if cleaned_suggestion:
                        new_suggestions.append(cleaned_suggestion)
                
                st.session_state.all_suggestions.extend(new_suggestions)
                st.session_state.suggestions_count += 1
                
            except Exception as e:
                st.error(f"生成回复时出错：{str(e)}")

    # 显示所有生成的建议
    if st.session_state.all_suggestions:
        st.write("### 所有建议的回复")
        for i, suggestion in enumerate(st.session_state.all_suggestions, 1):
            st.text_area(f"建议 {i}", value=suggestion, height=100)
