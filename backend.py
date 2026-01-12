import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(page_title="Kartog AI", page_icon="🗺️", layout="centered")

st.title("🗺️ Kartog AI")
st.markdown("##### *Mapping your skills to the professional landscape.*")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "graph_state" not in st.session_state:
    st.session_state.graph_state = {"messages": [], "active_agent": "advisor"}

with st.sidebar:
    st.header("Kartog Controls")
    st.markdown("Use the controls below to reset your journey.")

    if st.button("Start New Map", type="primary"):
        st.session_state.messages = []
        st.session_state.graph_state = {"messages": [], "active_agent": "advisor"}
        st.rerun()


@st.cache_resource
def load_graph():
    from app import app

    return app


try:
    agent_app = load_graph()
except Exception as e:
    st.error(f"Error loading backend: {e}")
    st.stop()


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Describe your skills or career goals..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    st.session_state.graph_state["messages"].append(HumanMessage(content=user_input))

    with st.chat_message("assistant"):
        with st.status("Charting course...", expanded=True) as status:
            try:
                result = agent_app.invoke(st.session_state.graph_state)
                st.session_state.graph_state = result

                last_msg = result["messages"][-1]

                if not last_msg.content and getattr(last_msg, "tool_calls", None):
                    response_text = "*Surveying external job databases...*"
                    status.write("Scouting terrain...")
                else:
                    response_text = last_msg.content
                    status.write("Drafting response...")

                current_agent = result.get("active_agent", "Kartog").upper()

                status.update(label="Route Found", state="complete", expanded=False)

            except Exception as e:
                status.update(label="Navigation Error", state="error")
                st.error(f"System Error: {e}")
                st.stop()

        formatted_response = f"**{current_agent}**: {response_text}"
        st.markdown(formatted_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": formatted_response}
        )
