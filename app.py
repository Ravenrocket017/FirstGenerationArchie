import streamlit as st
import requests
import json

# --- 設定頁面資訊 ---
st.set_page_config(page_title="ARK 智能助理", page_icon="🚢")

# --- 設定你的 Dify API 資訊 (建議在 Streamlit Secrets 設定，見下一步) ---
# 這裡先留空，我們等一下在後台填寫，這樣才安全
BASE_URL = st.secrets["DIFY_BASE_URL"]
API_KEY = st.secrets["DIFY_API_KEY"]

# --- 初始化 Session State (用來記住聊天記錄) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = ""

# --- 側邊欄 (可選，不需要可刪除) ---
with st.sidebar:
    st.markdown("### 關於 ARK")
    st.markdown("我是您的方舟計畫導航員，請隨時向我提問。")
    if st.button("清除對話"):
        st.session_state.messages = []
        st.session_state.conversation_id = ""
        st.rerun()

# --- 顯示歷史對話 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 處理使用者輸入 ---
if prompt := st.chat_input("請輸入您的問題..."):
    # 1. 顯示使用者輸入
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 呼叫 Dify API
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": {},
            "query": prompt,
            "response_mode": "streaming", # 開啟串流模式，像打字機一樣
            "conversation_id": st.session_state.conversation_id,
            "user": "streamlit-user"
        }

        try:
            response = requests.post(
                f"{BASE_URL}/chat-messages", 
                headers=headers, 
                json=payload, 
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data:'):
                            json_str = decoded_line[5:] # 去掉 'data:' 前綴
                            try:
                                data = json.loads(json_str)
                                # 獲取 conversation_id 以便延續對話
                                if "conversation_id" in data:
                                    st.session_state.conversation_id = data["conversation_id"]
                                # 獲取回答內容
                                if "answer" in data:
                                    full_response += data["answer"]
                                    message_placeholder.markdown(full_response + "▌")
                            except:
                                pass
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"連線錯誤: {str(e)}")
