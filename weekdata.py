import streamlit as st
import pandas as pd
import numpy as np
import openai
# ... existing imports ...

# 设置OpenAI API密钥
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = None

def calculate_overall_satisfaction(df):
    """计算总体满意率"""
    # 只统计评分列有数据的行
    df_valid = df.dropna(subset=['评分'])
    if len(df_valid) == 0:
        return 0
    satisfied = len(df_valid[df_valid['评分'].str.contains('优秀|合格', na=False)])
    return (satisfied / len(df_valid)) * 100

def calculate_accuracy(df):
    # 只统计两列都有数据的行
    valid_rows = df.dropna(subset=['人工SQU', '机器SQU'])
    manual_correct = valid_rows.apply(lambda row: str(row['人工SQU']) in str(row['机器SQU']), axis=1).sum()
    manual_incorrect = valid_rows.shape[0] - manual_correct
    accuracy = (manual_correct / (manual_correct + manual_incorrect)) * 100 if (manual_correct + manual_incorrect) > 0 else 0
    return {
        'manual_correct': manual_correct,
        'manual_incorrect': manual_incorrect,
        'accuracy': accuracy,
        'total_rows': len(df),
        'valid_rows': len(valid_rows)
    }

def calculate_model_stats(df):
    """计算模型统计数据"""
    try:
        # 过滤有效数据
        df_valid = df.dropna(subset=['问题标签', '评分', '机器打分'])
        
        # 区分随机样本和负样本
        random_samples = df_valid[df_valid['问题标签'] == '随机样本']
        negative_samples = df_valid[df_valid['问题标签'] == '负样本']
        
        # 计算各样本的统计数据
        random_stats = get_sample_stats(random_samples)
        negative_stats = get_sample_stats(negative_samples)
        
        return {
            'random': random_stats,
            'negative': negative_stats
        }
    except Exception as e:
        st.error(f'计算模型统计时发生错误: {str(e)}')
        return None

def get_sample_stats(df):
    excellent = len(df[df['评分'].str.contains('优秀', na=False)])
    qualified = len(df[df['评分'].str.contains('合格', na=False)])
    poor = len(df[df['评分'].str.contains('较差', na=False)])
    valid_samples = excellent + qualified + poor
    satisfaction = ((excellent + qualified) / valid_samples * 100) if valid_samples > 0 else 0
    
    # 直接使用机器打分列计算平均分
    avg_score = df['机器打分'].mean() if not pd.isna(df['机器打分'].mean()) else 0
    
    return {
        'total': len(df),
        'excellent': excellent,
        'qualified': qualified,
        'poor': poor,
        'satisfaction': satisfaction,
        'avg_score': avg_score
    }

def calculate_recall_stats(df):
    """计算知识库召回统计数据"""
    # 计算平均召回条数
    avg_recall = df['召回条数'].mean()
    
    # 计算有召回的占比
    df_recall = df.dropna(subset=['召回条数'])
    has_recall = len(df_recall[df_recall['召回条数'] > 0])
    no_recall = len(df_recall[df_recall['召回条数'] == 0])
    total_rows = len(df_recall)
    recall_ratio = (has_recall / total_rows) * 100 if total_rows > 0 else 0
    
    # 计算有召回和无召回的满意度，排除评分为空的数据
    df_valid = df.dropna(subset=['评分'])
    
    # 按召回条数分组计算满意度
    df_recall_1_3 = df_valid[(df_valid['召回条数'] >= 1) & (df_valid['召回条数'] <= 3)]
    df_recall_4_7 = df_valid[(df_valid['召回条数'] >= 4) & (df_valid['召回条数'] <= 7)]
    df_recall_8_10 = df_valid[(df_valid['召回条数'] >= 8) & (df_valid['召回条数'] <= 10)]
    df_no_recall = df_valid[df_valid['召回条数'] == 0]
    
    recall_1_3_satisfaction = calculate_satisfaction(df_recall_1_3)
    recall_4_7_satisfaction = calculate_satisfaction(df_recall_4_7)
    recall_8_10_satisfaction = calculate_satisfaction(df_recall_8_10)
    no_recall_satisfaction = calculate_satisfaction(df_no_recall)
    
    return {
        'avg_recall': avg_recall,
        'recall_ratio': recall_ratio,
        'recall_1_3_satisfaction': recall_1_3_satisfaction,
        'recall_4_7_satisfaction': recall_4_7_satisfaction,
        'recall_8_10_satisfaction': recall_8_10_satisfaction,
        'no_recall_satisfaction': no_recall_satisfaction,
        'total_with_recall': has_recall,
        'total_no_recall': no_recall,
        'total_recall_1_3': len(df_recall_1_3),
        'total_recall_4_7': len(df_recall_4_7),
        'total_recall_8_10': len(df_recall_8_10)
    }

def calculate_satisfaction(df):
    """计算满意度"""
    if len(df) == 0:
        return 0
    satisfied = len(df[df['评分'].str.contains('优秀|合格', na=False)])
    return (satisfied / len(df)) * 100

# 设置页面标题和布局
st.set_page_config(page_title="数据分析系统", layout="wide")

# 添加页面标题
st.title('数据分析系统 📊')

# 添加文件上传组件
uploaded_file = st.file_uploader("请上传CSV文件进行分析", type=['csv'], help="支持CSV格式文件")

if uploaded_file is not None:
    # 读取数据并显示加载进度
    with st.spinner('正在加载数据...'):
        df = pd.read_csv(uploaded_file)
    
    # 使用expander显示数据预览
    with st.expander("查看数据预览"):
        st.dataframe(df.head(), use_container_width=True)

    # 计算统计数据
    overall_satisfaction = calculate_overall_satisfaction(df)
    squ_accuracy = calculate_accuracy(df)
    model_stats = calculate_model_stats(df)
    recall_stats = calculate_recall_stats(df)

    if model_stats is None:
        st.error("无法计算模型统计数据")
    else:
        # 使用列布局展示分析结果
        st.subheader('📈 分析报告')
        
        # 总体满意率
        st.metric(
            label="总体满意率",
            value=f"{overall_satisfaction:.2f}%"
        )
        
        # SQU有效性分析
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="SQU模型准确率",
                value=f"{squ_accuracy['accuracy']:.2f}%"
            )
        with col2:
            st.metric(
                label="有效/不准确样本数",
                value=f"{squ_accuracy['manual_correct']}/{squ_accuracy['manual_incorrect']}"
            )

        # 随机样本分析
        st.subheader("随机样本分析")
        col3, col4, col5 = st.columns(3)
        with col3:
            st.metric("总样本数", model_stats['random']['total'])
        with col4:
            st.metric("人工打标满意率", f"{model_stats['random']['satisfaction']:.2f}%")
        with col5:
            st.metric("机器均分", f"{model_stats['random']['avg_score']:.2f}")

        # 负样本分析
        st.subheader("负样本分析")
        col6, col7, col8 = st.columns(3)
        with col6:
            st.metric("总样本数", model_stats['negative']['total'])
        with col7:
            st.metric("人工打标满意率", f"{model_stats['negative']['satisfaction']:.2f}%")
        with col8:
            st.metric("机器均分", f"{model_stats['negative']['avg_score']:.2f}")
            
        # 知识库召回分析
        st.subheader("知识库召回分析")
        col9, col10 = st.columns(2)
        with col9:
            st.metric("平均召回条数", f"{recall_stats['avg_recall']:.2f}")
        with col10:
            st.metric("有召回占比（召回内容大于等于1）", f"{recall_stats['recall_ratio']:.2f}% ({recall_stats['total_with_recall']}/{recall_stats['total_no_recall']})")
            
        col11, col12, col13, col14 = st.columns(4)
        with col11:
            st.metric("召回1~3条知识的满意度", f"{recall_stats['recall_1_3_satisfaction']:.2f}% ({recall_stats['total_recall_1_3']}组)")
        with col12:
            st.metric("召回4~7条知识的满意度", f"{recall_stats['recall_4_7_satisfaction']:.2f}% ({recall_stats['total_recall_4_7']}组)")
        with col13:
            st.metric("召回8~10条知识的满意度", f"{recall_stats['recall_8_10_satisfaction']:.2f}% ({recall_stats['total_recall_8_10']}组)")
        with col14:
            st.metric("无召回回答的满意度", f"{recall_stats['no_recall_satisfaction']:.2f}% ({recall_stats['total_no_recall']}组)")
            
        # 添加总结文案
        st.subheader("📋 分析总结")
        summary = f"""一、SQU有效性判断模型，准确率 {squ_accuracy['accuracy']:.2f}%：
总数据量：{squ_accuracy['total_rows']} 组 有效数据量：{squ_accuracy['valid_rows']} 组（排除空值后）
人工标注：准确 {squ_accuracy['manual_correct']} 组、不准确 {squ_accuracy['manual_incorrect']} 组

二、打分模型能力，共完成{squ_accuracy['total_rows']}条有效且反馈满意度：
随机样本（机器打分>6分）：共{model_stats['random']['total']}组， 优秀{model_stats['random']['excellent']}组、 合格{model_stats['random']['qualified']}组、 较差{model_stats['random']['poor']}组， 满意度{model_stats['random']['satisfaction']:.2f}%， 机器均分{model_stats['random']['avg_score']:.2f}分

负样本（机器打分<6分）：共{model_stats['negative']['total']}组， 优秀{model_stats['negative']['excellent']}组、 合格{model_stats['negative']['qualified']}组、 较差{model_stats['negative']['poor']}组， 满意度{model_stats['negative']['satisfaction']:.2f}%， 机器均分{model_stats['negative']['avg_score']:.2f}分

三、知识库召回分析：
平均召回条数：{recall_stats['avg_recall']:.2f}条，有召回占比（召回内容大于等于1）：{recall_stats['recall_ratio']:.2f}% ({recall_stats['total_with_recall']}/{recall_stats['total_no_recall']})
召回1~3条知识：{recall_stats['total_recall_1_3']}组，满意度{recall_stats['recall_1_3_satisfaction']:.2f}%
召回4~7条知识：{recall_stats['total_recall_4_7']}组，满意度{recall_stats['recall_4_7_satisfaction']:.2f}%
召回8~10条知识：{recall_stats['total_recall_8_10']}组，满意度{recall_stats['recall_8_10_satisfaction']:.2f}%
无召回样本：{recall_stats['total_no_recall']}组，满意度{recall_stats['no_recall_satisfaction']:.2f}%"""

        # 创建一个文本框和复制按钮的容器
        col_text, col_button = st.columns([4,1])
        with col_text:
            st.code(summary)
        with col_button:
            st.button("📋 复制总结", on_click=lambda: st.write(f'<script>navigator.clipboard.writeText(`{summary}`)</script>', unsafe_allow_html=True))
            
        # 添加可视化图表
        st.subheader("📊 数据可视化")
        
        # SQU有效性分析饼图
        col_pie1, col_pie2 = st.columns(2)
        
        with col_pie1:
            st.subheader("SQU模型准确性分布")
            fig_squ = {
                'data': [{
                    'values': [squ_accuracy['manual_correct'], squ_accuracy['manual_incorrect']],
                    'labels': ['有效样本', '不准确样本'],
                    'type': 'pie',
                    'hole': 0.4,
                }],
                'layout': {'title': 'SQU模型准确性分布'}
            }
            st.plotly_chart(fig_squ, use_container_width=True)
            
        with col_pie2:
            st.subheader("知识库召回情况分布")
            fig_recall = {
                'data': [{
                    'values': [recall_stats['total_with_recall'], recall_stats['total_no_recall']],
                    'labels': ['有召回', '无召回'],
                    'type': 'pie',
                    'hole': 0.4,
                }],
                'layout': {'title': '知识库召回情况分布'}
            }
            st.plotly_chart(fig_recall, use_container_width=True)

# 在显示所有分析结果后添加对话功能
if uploaded_file is not None:
    st.divider()
    st.subheader("💬 与数据对话")
    
    # 添加API Key输入框
    api_key = st.text_input("请输入OpenAI API Key", type="password", key="api_key_input")
    if api_key:
        st.session_state.openai_api_key = api_key
        openai.api_key = api_key
    
    # 初始化聊天历史
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 聊天输入
    if prompt := st.chat_input("请输入您的问题"):
        if not st.session_state.openai_api_key:
            st.error("请先输入OpenAI API Key")
        else:
            # 将用户问题添加到聊天历史
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # 显示用户问题
            with st.chat_message("user"):
                st.markdown(prompt)

            # 显示助手回复
            with st.chat_message("assistant"):
                try:
                    # 将DataFrame转换为字符串描述
                    df_info = f"""
                    数据集包含以下列：{', '.join(df.columns)}
                    总行数：{len(df)}
                    
                    数据统计信息：
                    - 总体满意率: {overall_satisfaction:.2f}%
                    - SQU模型准确率: {squ_accuracy['accuracy']:.2f}%
                    - 平均召回条数: {recall_stats['avg_recall']:.2f}
                    """
                    
                    message_placeholder = st.empty()
                    # 使用新版OpenAI API
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": f"你是一个数据分析助手。以下是数据集的信息：\n{df_info}"},
                            {"role": "user", "content": prompt}
                        ],
                        stream=True
                    )
                    
                    full_response = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                    
                    # 将助手回复添加到聊天历史
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                except Exception as e:
                    st.error(f"生成回复时发生错误: {str(e)}")
