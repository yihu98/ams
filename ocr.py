import streamlit as st
import requests
import re
import json
from bs4 import BeautifulSoup
import time
import os
from openai import OpenAI
import codecs

st.set_page_config(page_title="小红书文字提取工具", page_icon="📝", layout="wide")

st.title("📝 小红书文字提取工具")
st.markdown("✨ 专门提取小红书图片中的文字内容")

# 侧边栏设置
with st.sidebar:
    st.header("⚙️ 设置")
    user_agent = st.text_input(
        "User-Agent (可选)", 
        value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        help="自定义User-Agent，用于模拟浏览器请求"
    )
    
    st.markdown("---")
    st.subheader("🔍 OCR设置")
    
    # 设置API Key
    ark_api_key = st.text_input(
        "豆包API Key", 
        value="79329882-cb1a-4b0a-be47-765e83281ea4",
        type="password",
        help="豆包API Key，用于调用视觉大模型"
    )
    
    # 模型选择
    model_id = st.text_input(
        "豆包模型ID",
        value="ep-20250512154520-xv6s9",
        help="豆包推理接入点ID"
    )

# URL清理函数
def clean_image_url(url):
    """清理和解码图片URL"""
    if not url:
        return ""
    
    try:
        # 移除URL前的@符号
        url = url.lstrip('@').strip()
        
        # 处理Unicode转义字符
        if '\\u' in url:
            url = codecs.decode(url, 'unicode_escape')
        
        # 如果是JSON字符串，尝试解析
        if url.startswith('{') and url.endswith('}'):
            try:
                json_obj = json.loads(url)
                if 'urlDefault' in json_obj:
                    url = json_obj['urlDefault']
                elif 'url' in json_obj:
                    url = json_obj['url']
                # 再次处理转义字符
                if '\\u' in url:
                    url = codecs.decode(url, 'unicode_escape')
            except:
                pass
        
        # 确保URL是http开头
        if url.startswith('//'):
            url = 'http:' + url
        elif not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        return url
    except:
        return url

# 初始化豆包客户端
def init_doubao_client(api_key):
    """初始化豆包视觉大模型客户端"""
    try:
        client = OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key,
        )
        return client
    except Exception as e:
        st.error(f"豆包客户端初始化失败: {str(e)}")
        return None

# 主界面
st.markdown("### 📝 请输入小红书链接")
xhs_url = st.text_input(
    "小红书链接",
    placeholder="https://www.xiaohongshu.com/explore/...",
    help="支持小红书笔记链接"
)

# 提取小红书ID的函数
def extract_note_id(url):
    """从小红书链接中提取笔记ID"""
    patterns = [
        r'explore/([a-f0-9]+)',
        r'discovery/item/([a-f0-9]+)',
        r'/([a-f0-9]{24})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# 使用豆包API识别图片文字
def extract_text_from_image_doubao(img_url, client, model_id):
    """使用豆包视觉大模型从图片中提取文字"""
    if client is None:
        return "豆包客户端未初始化"
    
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": img_url
                            },
                        },
                        {
                            "type": "text", 
                            "text": "请识别并提取这张图片中的所有文字内容，包括中文、英文、数字等。请按照图片中文字的布局顺序，逐行返回识别的文字，保持原有的换行结构。如果没有文字就返回'无文字'。"
                        },
                    ],
                }
            ],
        )
        
        if response.choices and response.choices[0].message:
            text_content = response.choices[0].message.content.strip()
            return text_content if text_content and text_content != "无文字" else "未识别到文字"
        else:
            return "API响应为空"
            
    except Exception as e:
        return f"豆包API调用错误: {str(e)}"

# 抓取小红书内容的函数
def fetch_xhs_content(url):
    """抓取小红书内容"""
    try:
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尝试从不同位置提取内容
        content_data = {}
        
        # 提取标题
        title_selectors = [
            'meta[property="og:title"]',
            'title',
            '.note-title',
            'h1'
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                if selector.startswith('meta'):
                    content_data['title'] = title_element.get('content', '').strip()
                else:
                    content_data['title'] = title_element.get_text().strip()
                if content_data['title']:
                    break
        
        # 提取描述/内容
        desc_selectors = [
            'meta[property="og:description"]',
            'meta[name="description"]',
            '.note-content',
            '.desc'
        ]
        
        for selector in desc_selectors:
            desc_element = soup.select_one(selector)
            if desc_element:
                if selector.startswith('meta'):
                    content_data['description'] = desc_element.get('content', '').strip()
                else:
                    content_data['description'] = desc_element.get_text().strip()
                if content_data['description']:
                    break
        
        # 提取图片 - 增强版
        img_selectors = [
            'meta[property="og:image"]',
            'meta[name="twitter:image"]',
            '.note-image img',
            '.image-container img',
            '.photo-item img',
            '.swiper-slide img',
            'img[src*="ci.xiaohongshu.com"]',
            'img[src*="sns-webpic-qc.xhscdn.com"]',
            'img[src*="xhscdn.com"]',
            'img[data-src*="xhscdn.com"]',
            'img[data-original*="xhscdn.com"]',
            'img'  # 作为备选，获取所有img标签
        ]
        
        images = []
        
        for selector in img_selectors:
            if selector.startswith('meta'):
                img_element = soup.select_one(selector)
                if img_element:
                    img_url = img_element.get('content', '')
                    if img_url and 'xhs' in img_url.lower():
                        cleaned_url = clean_image_url(img_url)
                        images.append(cleaned_url)
            else:
                img_elements = soup.select(selector)
                for img in img_elements:
                    # 尝试多个属性获取图片URL
                    img_url = (img.get('src', '') or 
                              img.get('data-src', '') or 
                              img.get('data-original', '') or
                              img.get('data-lazy', '') or
                              img.get('data-url', ''))
                    
                    if img_url:
                        # 过滤掉明显不是内容图片的URL
                        if ('xhs' in img_url.lower() and
                            not any(x in img_url.lower() for x in ['avatar', 'head', 'icon', 'logo', 'badge'])):
                            cleaned_url = clean_image_url(img_url)
                            if cleaned_url not in images:
                                images.append(cleaned_url)
        
        content_data['images'] = images[:10]  # 限制最多10张图片
        
        # 尝试从页面源码中提取JSON数据以获取更多图片
        script_tags = soup.find_all('script')
        json_images_found = []
        
        for script in script_tags:
            if script.string:
                # 尝试多种JSON数据提取方式
                patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                    r'window\.__NUXT__\s*=\s*({.+?});',
                    r'"imageList"\s*:\s*\[([^\]]+)\]',
                    r'"urlDefault"\s*:\s*"([^"]+)"',
                    r'"url"\s*:\s*"(https://[^"]*xhscdn[^"]*)"'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, script.string)
                    for match in matches:
                        if pattern == patterns[0] or pattern == patterns[1]:  # 完整JSON
                            try:
                                data = json.loads(match)
                                # 递归搜索图片URL
                                def find_images_in_json(obj, path=""):
                                    if isinstance(obj, dict):
                                        for key, value in obj.items():
                                            if key in ['urlDefault', 'url', 'src'] and isinstance(value, str) and 'xhscdn' in value:
                                                cleaned_url = clean_image_url(value)
                                                json_images_found.append(cleaned_url)
                                                if cleaned_url not in content_data['images']:
                                                    content_data['images'].append(cleaned_url)
                                            else:
                                                find_images_in_json(value, f"{path}.{key}")
                                    elif isinstance(obj, list):
                                        for i, item in enumerate(obj):
                                            find_images_in_json(item, f"{path}[{i}]")
                                
                                find_images_in_json(data)
                            except:
                                continue
                        else:  # 直接URL匹配
                            if 'xhscdn' in match:
                                cleaned_url = clean_image_url(match)
                                if cleaned_url not in content_data['images']:
                                    json_images_found.append(cleaned_url)
                                    content_data['images'].append(cleaned_url)
        
        # 最后的备用方案：直接从页面源码中搜索所有可能的图片URL
        if len(content_data['images']) == 0:
            backup_images = []
            # 使用正则表达式搜索所有包含xhscdn的URL
            url_patterns = [
                r'https://[^"\s]*xhscdn[^"\s]*\.(?:jpg|jpeg|png|webp|gif)',
                r'https://[^"\s]*ci\.xiaohongshu[^"\s]*\.(?:jpg|jpeg|png|webp|gif)',
                r'"(https://[^"]*xhscdn[^"]*)"',
                r"'(https://[^']*xhscdn[^']*)'"
            ]
            
            page_text = response.text
            for pattern in url_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    cleaned_url = clean_image_url(match)
                    if cleaned_url not in backup_images and len(backup_images) < 10:
                        backup_images.append(cleaned_url)
            
            if backup_images:
                content_data['images'].extend(backup_images[:5])  # 添加前5个备用图片
        
        return content_data
        
    except requests.RequestException as e:
        return {'error': f'网络请求错误: {str(e)}'}
    except Exception as e:
        return {'error': f'解析错误: {str(e)}'}

# 处理链接输入
if xhs_url:
    if not xhs_url.startswith(('http://', 'https://')):
        xhs_url = 'https://' + xhs_url
    
    # 验证是否为小红书链接
    if 'xiaohongshu.com' not in xhs_url and 'xhslink.com' not in xhs_url:
        st.error("❌ 请输入有效的小红书链接")
    else:
        # 提取笔记ID
        note_id = extract_note_id(xhs_url)
        if note_id:
            st.info(f"📋 检测到笔记ID: {note_id}")
        
        # 开始抓取按钮
        if st.button("🚀 开始提取文字", type="primary"):
            # 检查必要参数
            if not ark_api_key:
                st.error("❌ 请输入豆包API Key")
            elif not model_id:
                st.error("❌ 请输入豆包模型ID")
            else:
                # 初始化豆包客户端
                with st.spinner("正在初始化豆包客户端..."):
                    doubao_client = init_doubao_client(ark_api_key)
                
                if doubao_client:
                    with st.spinner("正在抓取内容，请稍候..."):
                        content = fetch_xhs_content(xhs_url)
                        
                        if 'error' in content:
                            st.error(f"抓取失败: {content['error']}")
                            st.markdown("""
                            ### 💡 抓取建议
                            - 确保链接有效且可访问
                            - 小红书可能有反爬虫机制，请稍后重试
                            - 尝试使用不同的User-Agent
                            - 某些私密内容可能无法访问
                            """)
                        else:
                            st.success("✅ 抓取成功!")
                            
                            # 显示基本信息
                            st.markdown("---")
                            st.markdown("### 📄 基本信息")
                            
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                # 显示标题
                                if content.get('title'):
                                    st.markdown("#### 📝 标题")
                                    st.write(content['title'])
                                
                                # 显示描述/内容
                                if content.get('description'):
                                    st.markdown("#### 📖 内容描述")
                                    st.write(content['description'])
                            
                            with col2:
                                st.markdown("#### 📊 统计信息")
                                st.metric("图片数量", len(content.get('images', [])))
                                if content.get('title'):
                                    st.metric("标题长度", len(content['title']))
                                if content.get('description'):
                                    st.metric("描述长度", len(content['description']))
                            
                            # 图片文字提取
                            if content.get('images'):
                                st.markdown("---")
                                st.markdown("### 🔍 图片文字提取")
                                st.write(f"共发现 {len(content['images'])} 张图片，正在提取文字...")
                                
                                # OCR识别进度条
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                all_ocr_texts = []  # 存储所有OCR识别的文字
                                
                                # 处理每张图片
                                for idx, img_url in enumerate(content['images']):
                                    # 更新进度
                                    progress = (idx + 1) / len(content['images'])
                                    progress_bar.progress(progress)
                                    status_text.text(f"正在识别图片 {idx+1}/{len(content['images'])}...")
                                    
                                    # 使用豆包API进行文字识别
                                    ocr_text = extract_text_from_image_doubao(img_url, doubao_client, model_id)
                                    
                                    # 显示每张图片的识别结果
                                    with st.container():
                                        st.markdown(f"#### 图片 {idx+1} 识别结果")
                                        st.text(f"URL: {img_url}")
                                        
                                        # 检查是否是有效的文字识别结果
                                        is_valid_text = (ocr_text and 
                                                        ocr_text != "未识别到文字" and 
                                                        not ocr_text.startswith("豆包API调用错误") and
                                                        not ocr_text.startswith("API响应为空") and
                                                        not ocr_text.startswith("豆包客户端未初始化") and
                                                        ocr_text != "无文字")
                                        
                                        if is_valid_text:
                                            st.success("✅ 识别成功")
                                            st.text_area(f"图片{idx+1}文字内容", ocr_text, height=150, key=f"ocr_{idx}")
                                            all_ocr_texts.append(f"【图片{idx+1}】\n{ocr_text}")
                                        else:
                                            st.warning("⚠️ 未识别到文字内容")
                                            if ocr_text and (ocr_text.startswith("豆包API调用错误") or 
                                                           ocr_text.startswith("API响应为空") or 
                                                           ocr_text.startswith("豆包客户端未初始化")):
                                                st.error(f"错误信息: {ocr_text}")
                                        
                                        st.markdown("---")
                                
                                # 清除进度条
                                progress_bar.empty()
                                status_text.empty()
                                
                                # 显示所有OCR结果汇总
                                if all_ocr_texts or content.get('title') or content.get('description'):
                                    st.markdown("### 📝 所有文字汇总")
                                    
                                    # 构建JSON格式的汇总内容
                                    summary_data = {
                                        "标题": content.get('title', ''),
                                        "笔记内容": content.get('description', ''),
                                        "图片文字": {}
                                    }
                                    
                                    # 添加图片文字识别结果
                                    if all_ocr_texts:
                                        for idx, ocr_text in enumerate(all_ocr_texts):
                                            # 提取图片编号和文字内容
                                            if ocr_text.startswith("【图片"):
                                                # 分割出图片编号和内容
                                                lines = ocr_text.split("\n", 1)
                                                img_key = lines[0].replace("【", "").replace("】", "")
                                                img_content = lines[1] if len(lines) > 1 else ""
                                                summary_data["图片文字"][img_key] = img_content
                                    
                                    # 显示JSON格式的汇总
                                    combined_json = json.dumps(summary_data, ensure_ascii=False, indent=2)
                                    st.code(combined_json, language="json")
                                    
                                    # 也提供文本格式的选项
                                    with st.expander("查看文本格式汇总"):
                                        text_summary = f"标题: {summary_data['标题']}\n\n"
                                        text_summary += f"笔记内容: {summary_data['笔记内容']}\n\n"
                                        if summary_data['图片文字']:
                                            text_summary += "图片文字:\n"
                                            for img_key, img_text in summary_data['图片文字'].items():
                                                text_summary += f"\n【{img_key}】\n{img_text}\n"
                                        st.text_area("文本格式汇总", text_summary, height=300)
                                    
                                    combined_text = combined_json
                                    
                                    # 将OCR结果添加到内容数据中
                                    content['ocr_texts'] = all_ocr_texts
                                    content['combined_ocr_text'] = combined_text
                                    content['summary_data'] = summary_data
                                    
                                    # 导出功能
                                    st.markdown("---")
                                    st.markdown("### 📥 导出选项")
                                    
                                    export_col1, export_col2 = st.columns(2)
                                    
                                    with export_col1:
                                        # 导出文字为JSON
                                        if st.button("📝 导出汇总JSON"):
                                            st.download_button(
                                                label="下载JSON汇总文件",
                                                data=combined_text,
                                                file_name=f"xiaohongshu_汇总_{note_id or 'content'}.json",
                                                mime="application/json"
                                            )
                                        
                                        # 导出文字为文本格式
                                        if st.button("📄 导出文本格式"):
                                            text_content = f"标题: {summary_data['标题']}\n\n"
                                            text_content += f"笔记内容: {summary_data['笔记内容']}\n\n"
                                            if summary_data['图片文字']:
                                                text_content += "图片文字:\n"
                                                for img_key, img_text in summary_data['图片文字'].items():
                                                    text_content += f"\n【{img_key}】\n{img_text}\n"
                                            
                                            st.download_button(
                                                label="下载文字文件",
                                                data=text_content,
                                                file_name=f"xiaohongshu_文字_{note_id or 'content'}.txt",
                                                mime="text/plain"
                                            )
                                    
                                    with export_col2:
                                        # 导出完整JSON
                                        if st.button("📄 导出完整数据"):
                                            json_str = json.dumps(content, ensure_ascii=False, indent=2)
                                            st.download_button(
                                                label="下载JSON文件",
                                                data=json_str,
                                                file_name=f"xiaohongshu_完整_{note_id or 'content'}.json",
                                                mime="application/json"
                                            )
                                elif not content.get('title') and not content.get('description'):
                                    st.warning("⚠️ 所有图片都未能识别到文字内容，且未获取到基本信息")
                            else:
                                st.warning("⚠️ 未找到任何图片")

# 使用说明
with st.expander("📚 使用说明"):
    st.markdown("""
    ### 如何使用
    1. 在侧边栏输入您的豆包API Key和模型ID
    2. 在小红书中找到想要提取文字的笔记
    3. 复制笔记链接（通常以 https://www.xiaohongshu.com/explore/ 开头）
    4. 将链接粘贴到上方输入框中
    5. 点击"开始提取文字"按钮
    6. 等待文字识别完成，查看结果
    
    ### 功能特色 ✨
    - **专业文字提取**: 专门用于提取图片中的文字内容
    - **豆包大模型**: 使用先进的视觉大模型，识别准确率高
    - **批量处理**: 自动处理笔记中的所有图片
    - **文字汇总**: 将所有图片的文字内容合并展示
    - **多格式导出**: 支持纯文字和JSON格式导出
    
    ### 支持的链接格式
    - https://www.xiaohongshu.com/explore/...
    - https://www.xiaohongshu.com/discovery/item/...
    - 其他小红书分享链接
    
    ### 技术说明
    - 使用豆包视觉大模型进行文字识别
    - 支持中英文混合识别
    - 基于云端API，识别速度快
    - 自动处理图片URL编码问题
    
    ### 注意事项
    - 请遵守小红书的使用条款
    - 仅用于个人学习和研究目的
    - 部分内容可能因隐私设置无法抓取
    - 文字识别准确性取决于图片质量
    - 需要有效的豆包API Key和模型ID
    """)

# 免责声明
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
⚠️ 免责声明：本工具仅供学习交流使用，请遵守相关法律法规和平台规则。使用者需自行承担相应责任。<br>
🔍 文字识别功能基于豆包视觉大模型实现，识别结果仅供参考。
</div>
""", unsafe_allow_html=True) 
