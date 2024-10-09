import streamlit as st
import pandas as pd
from GettingTeamData import UpdatingActions

# Setting the title of the PMR App in web browser
st.set_page_config(page_title='Bolts Post-Match Review App')


st.sidebar.success('Select a page above.')

# this updates actions
combined_actions = UpdatingActions()

combined_actions.dropna(subset= ['Team Name'],inplace=True)
combined_actions.reset_index(drop=True, inplace=True)

combined_actions['Match Date'] = pd.to_datetime(combined_actions['Match Date']).dt.strftime('%m/%d/%Y')

st.title("Bolts Post-Match Review App")

st.markdown("Select the Team, Opponent, and Date (Optional) to See the Post-Match Review")

# Selecting the Bolts team
teams = sorted(list(combined_actions['Team Name'].unique()))

selected_team = st.session_state.get('selected_team', teams[0])
if selected_team not in teams:
    selected_team = teams[0]  # Default to the first date if not found

selected_team = st.selectbox('Choose the Bolts Team:', teams, index=teams.index(selected_team))
st.session_state['selected_team'] = selected_team

combined_actions = combined_actions.loc[combined_actions['Team Name'] == st.session_state['selected_team']]

# Selecting the opponent team
opps = list(combined_actions['Opposition'].unique())

selected_opp = st.session_state.get('selected_opp', opps[0])
if selected_opp not in opps:
    selected_opp = opps[0]  # Default to the first date if not found
selected_opp = st.selectbox('Choose the Opposition:', opps, index=opps.index(selected_opp))
st.session_state['selected_opp'] = selected_opp

combined_actions = combined_actions.loc[combined_actions['Opposition'] == st.session_state['selected_opp']]

# Selecting the date
dates = list(combined_actions['Match Date'].unique())

# Check if the selected date in the session state exists in the list of dates
selected_date = st.session_state.get('selected_date', dates[0])
if selected_date not in dates:
    selected_date = dates[0]  # Default to the first date if not found

# Create the selectbox for the date
selected_date = st.selectbox('Choose the Date (if necessary)', dates, index=dates.index(selected_date))
st.session_state['selected_date'] = selected_date


st.session_state["selected_team"] = selected_team
st.session_state["selected_opp"] = selected_opp
st.session_state["selected_date"] = selected_date
