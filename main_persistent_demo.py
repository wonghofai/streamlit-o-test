import streamlit as st
import requests

def get_access_token():
  CLIENT_ID = st.session_state['aws_client_id']
  CLIENT_SECRET = st.session_state['aws_client_secret']
  response = requests.post(
    'https://us-east-1sbq9h01gm.auth.us-east-1.amazoncognito.com/oauth2/token',
    data=f"grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&scope=default-m2m-resource-server-nvyb8z/read",
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  return response.json()['access_token']

def get_all_sessions():
  USER_ID = st.session_state['user_id']
  ENDPOINT = st.session_state['aws_endpoint']
  ACCESS_TOKEN = get_access_token()
  response = requests.get(
    f"{ENDPOINT}/session/{USER_ID}",
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
  )
  print(f"[get_all_sessions] {response} {response.json()}")
  return response.json()

def call_create_session(user_id, session_id=None):
  ENDPOINT = st.session_state['aws_endpoint']
  ACCESS_TOKEN = get_access_token()
  print(f"[call_create_session] user_id: {user_id} session_id: {session_id}")
  json_dicts = {"user_id": user_id}
  if session_id is not None:
    json_dicts['session_id'] = session_id

  response = requests.post(
    f"{ENDPOINT}/session/start",
    json=json_dicts,
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
  )
  return response.json()

def call_resume_session(session_id, answer):
  ENDPOINT = st.session_state['aws_endpoint']
  ACCESS_TOKEN = get_access_token()
  response = requests.post(
    f"{ENDPOINT}/session/answer",
    json={"session_id": session_id, "answer": answer},
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
  ) 
  return response.json()

def call_get_session_data(session_id, data_type):
  ENDPOINT = st.session_state['aws_endpoint']
  ACCESS_TOKEN = get_access_token()
  response = requests.post(
    f"{ENDPOINT}/session/data",
    json={"session_id": session_id, "data_type": data_type},
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
  ) 
  return response.json()

def message_callback(message):
  with st.chat_message("assistant"):
    response = st.write(message)
  # Add assistant message to chat history
  st.session_state.messages.append({"role": "assistant", "content": message})

def display_course_outline():
  response = call_get_session_data(st.session_state['session_id'], "course_outline")
  if 'data' in response:
    st.write(f"=====> course_outline:\n\n {response['data']}")

def go_to_session():
  st.title("Dynamic Questioning App")
  st.write("Welcome to the Dynamic Questioning Example!")

  # Initialize chat history
  if "messages" not in st.session_state:
      st.session_state.messages = []

  # Questions History
  if 'questions_history' not in st.session_state:
    print("[start_streamlit_app] clear questions_history")
    st.session_state['questions_history'] = []

  if 'session_in_progress' not in st.session_state:
    if 'session_id' not in st.session_state:
      USER_ID = st.session_state['user_id']
      print(f"[start_streamlit_app] creating session {USER_ID}")
      response = call_create_session(USER_ID)
      print(f"[start_streamlit_app] {response}")
      if 'session_id' in response:
        st.session_state['session_id'] = response['session_id']
        st.write(f"=====> session_id: {st.session_state['session_id']}")
      if 'question' in response:
        message_callback(response['question'])
        st.session_state['session_in_progress'] = True
    else:
      USER_ID = st.session_state['user_id']
      print(f"[start_streamlit_app] resume session {USER_ID} {st.session_state['session_id']}")
      response = call_create_session(USER_ID, st.session_state['session_id'])
      print(f"[start_streamlit_app] resume session {response}")
      if 'question' in response:
        message_callback(response['question'])
        st.session_state['session_in_progress'] = True
      else:
        display_course_outline()
  else:
    if 'session_id' in st.session_state:
      st.write(f"=====> session_id: {st.session_state['session_id']}")
      display_course_outline()

  # Display chat messages from history on app rerun
  for message in st.session_state.messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])

  if answer := st.chat_input():
    # Display user message in chat message container
    with st.chat_message("user"):
      st.markdown(answer)
      # Add user message to chat history
      st.session_state.messages.append({"role": "user", "content": answer})
      # Resume Mindmap Graph with user message
    response = call_resume_session(st.session_state['session_id'], answer)
    if 'question' in response:
      message_callback(response['question'])
    else:
      display_course_outline()
  pass

if __name__ == "__main__":
  print(f"[main] session_state: {st.session_state}")

  if 'aws_endpoint' not in st.session_state or 'aws_client_id' not in st.session_state or 'aws_client_secret' not in st.session_state or 'user_id' not in st.session_state:
    endpoint = st.sidebar.text_input("oasis-zeus Endpoint", value="")
    client_id = st.sidebar.text_input("aws-client-id", value="")
    client_secret = st.sidebar.text_input("aws-client-secret", value="")
    st.sidebar.divider()
    user_id = st.sidebar.text_input("user-id", value="")
    user_submitted_pressed =st.sidebar.button("Login")
    if user_submitted_pressed:
      st.session_state['aws_endpoint'] = endpoint
      st.session_state['aws_client_id'] = client_id
      st.session_state['aws_client_secret'] = client_secret
      st.session_state['user_id'] = user_id
      st.rerun()
  else:
    if 'session_id' in st.session_state:
      st.sidebar.empty()
      end_session_pressed =st.sidebar.button("End Session")
      if end_session_pressed:
        # TODO: call end session
        endpoint = st.session_state['aws_endpoint']
        client_id = st.session_state['aws_client_id']
        client_secret = st.session_state['aws_client_secret']
        user_id = st.session_state['user_id']
        st.session_state.clear()
        st.session_state['aws_endpoint'] = endpoint
        st.session_state['aws_client_id'] = client_id
        st.session_state['aws_client_secret'] = client_secret
        st.session_state['user_id'] = user_id
        st.rerun()
      go_to_session()
    else:
      st.sidebar.empty()
      logout_pressed =st.sidebar.button("Logout")
      st.sidebar.divider()
      if logout_pressed:
        st.session_state.clear()
        st.rerun()
      new_session_pressed =st.sidebar.button("New Session")
      all_previos_sessions = get_all_sessions()
      option = st.sidebar.selectbox(
          "Previous Session",
          all_previos_sessions,
          index=None,
          placeholder="Select Previous Session...",
      )

      if option:
        print(f"[{option}]")
        resume_session_pressed = st.sidebar.button("Resume Session")
        if resume_session_pressed:
          st.session_state['session_id'] = option
          go_to_session()
          st.rerun()

      if new_session_pressed:
        go_to_session()
        st.rerun()
