import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage


with st.sidebar:
    st.header("Controls")
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.session_state.graph_state = {"messages": [], "active_agent": "advisor"}
        st.rerun()


st.set_page_config(page_title="Career Agent")
st.title("AI Career Architect & Scout")


if "messages" not in st.session_state:
    st.session_state.messages = []
if "graph_state" not in st.session_state:
    st.session_state.graph_state = {"messages": [], "active_agent": "advisor"}


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


if user_input := st.chat_input("Tell me about your skills..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    st.session_state.graph_state["messages"].append(HumanMessage(content=user_input))

    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            try:
                result = agent_app.invoke(st.session_state.graph_state)

                st.session_state.graph_state = result

                last_msg = result["messages"][-1]

                if not last_msg.content and getattr(last_msg, "tool_calls", None):
                    response_text = "*Checking the database for opportunities...*"
                else:
                    response_text = last_msg.content

                current_agent = result.get("active_agent", "System").upper()
                formatted_response = f"**{current_agent}**: {response_text}"

                st.markdown(formatted_response)

                st.session_state.messages.append(
                    {"role": "assistant", "content": formatted_response}
                )

            except Exception as e:
                st.error(f"An error occurred: {e}")
