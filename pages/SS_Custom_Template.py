import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from plotly_football_pitch import make_pitch_figure, PitchDimensions
import plotly_football_pitch as pfp
from xGModel import xGModel
import plotly.graph_objs as go
import glob
import os
from GettingPSDGradeData import getting_PSD_grade_data

selected_team = st.session_state['selected_team']
selected_opp = st.session_state['selected_opp']
selected_date = st.session_state['selected_date']



psd_grades = getting_PSD_grade_data()
psd_grades = psd_grades.loc[(psd_grades['Team Name'] == selected_team) & (psd_grades['Opposition'] == selected_opp) & (psd_grades['Match Date'] == selected_date)].reset_index(drop=True)
psd_grades[['Tackle', 'Unsucc Tackle', 'Stand. Tackle', 'Unsucc Stand. Tackle', 'Goal', 'Goal Against']] = psd_grades[['Tackle', 
'Unsucc Tackle', 'Stand. Tackle', 'Unsucc Stand. Tackle', 'Goal', 'Goal Against']].astype(float)
psd_grades[['Goal', 'Goal Against']] = psd_grades[['Goal', 'Goal Against']].astype(int)
psd_grades['Total Tackles'] = psd_grades['Tackle'] + psd_grades['Stand. Tackle']

bolts_score = psd_grades['Goal'].sum()
opp_score = psd_grades['Goal Against'].sum()



st.markdown(f"<h2 style='text-align: center;'>Bolts: {bolts_score}&nbsp;&nbsp;{selected_opp}: {opp_score}</h2>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align: center;'>Date: {selected_date}</h4>", unsafe_allow_html=True)


psd_grades = psd_grades[['Player Full Name', 'Pass Completion ', 'Dribble', 'Total Tackles']]
st.write(psd_grades)

folder_path = 'Bolts-SS/xG Input Files'

# Find all CSV files in the folder
csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

# List to hold individual DataFrames
df_list = []

# Loop through the CSV files and read them into DataFrames
for file in csv_files:
    df = pd.read_csv(file)
    df_list.append(df)

# Concatenate all DataFrames into a single DataFrame
fc_python = pd.concat(df_list, ignore_index=True)

# Making sure everything is aligned on one side
def flip_coordinates(x, y):
    # Flip x and y coordinates horizontally
    flipped_x = field_dim - x
    flipped_y = field_dim - y  # y remains unchanged in this transformation
    
    return flipped_x, flipped_y

field_dim = 100
# Iterating through coordinates and making them on one side
flipped_points = []
for index, row in fc_python.iterrows():
    if row['X'] < 50:
        flipped_x, flipped_y = flip_coordinates(row['X'], row['Y'])
        fc_python.at[index, 'X'] = flipped_x
        fc_python.at[index, 'Y'] = flipped_y


# Path to the folder containing CSV files
folder_path = 'Bolts-SS/Actions PSD'

# Find all CSV files in the folder
csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

# List to hold individual DataFrames
df_list = []

# Loop through the CSV files and read them into DataFrames
for file in csv_files:
    df = pd.read_csv(file)
    df.columns = df.loc[4]
    df = df.loc[5:].reset_index(drop=True)
    df_list.append(df)

# Concatenate all DataFrames into a single DataFrame
actions = pd.concat(df_list, ignore_index=True)
actions['Match Date'] = pd.to_datetime(actions['Match Date']).dt.strftime('%m/%d/%Y')
actions.loc[actions['Opposition'] == 'St Louis', 'Match Date'] = '12/09/2023'

# creating copies to work on
full_actions = actions.copy()
entire_actions = actions.copy()


full_actions = full_actions.loc[(full_actions['Team'] == selected_team) & (full_actions['Opposition'] == selected_opp) & (full_actions['Match Date'] == selected_date)].reset_index(drop=True)
full_actions_copy = full_actions.copy()
full_actions_copy2 = full_actions.copy()

# these are the ideal columns
cols = ['Player Full Name', 'Team', 'Match Date', 'Opposition', 'Action', 'Time', 'Video Link']
xg_actions = actions[cols]

# these are the shots we want
wanted_actions = ['Att Shot Blockd', 'Blocked Shot', 'Goal', 'Goal Against', 'Header on Target', 
                  'Header off Target', 'Opp Effort on Goal', 'Save Held', 'Save Parried', 'Shot off Target', 
                  'Shot on Target']
xg_actions = xg_actions.loc[xg_actions['Action'].isin(wanted_actions)].reset_index(drop=True)
# renaming for the join
xg_actions.rename(columns={'Team': 'Bolts Team'}, inplace=True)

# this is handeling duplicated PlayerStatData shots 
temp_df = pd.DataFrame(columns=xg_actions.columns)
prime_actions = ['Opp Effort on Goal', 'Shot on Target']
remove_indexes = []
for index in range(len(xg_actions) - 1):
    if xg_actions.loc[index, 'Time'] == xg_actions.loc[index+1, 'Time']:
        temp_df = pd.concat([temp_df, xg_actions.loc[[index]], xg_actions.loc[[index + 1]]], ignore_index=False)
        bye1 = temp_df.loc[temp_df['Action'].isin(prime_actions)]
        # these are the indexes we want to remove
        remove_indexes.extend(bye1.index)
        
    temp_df = pd.DataFrame(columns=xg_actions.columns)     

# this is a copy with the removed duplicated PSD shots
actions_new = xg_actions.copy()
actions_new = actions_new.drop(remove_indexes).reset_index(drop=True) 

fc_python['Match Date'] = pd.to_datetime(fc_python['Match Date']).dt.strftime('%m/%d/%Y')

# combining into xG dataframe we want
combined_xg = pd.merge(fc_python, actions_new, on=['Bolts Team', 'Match Date', 'Time'], how='inner')

xg = xGModel(combined_xg)


xg = xg.loc[(xg['Bolts Team'] == selected_team) & (xg['Opposition'] == selected_opp) & (xg['Match Date'] == selected_date)]

xg_data = xg.copy()


custom_order = ['Shot', 'Blocked', 'SOT', 'SOT Far Post', 'SOT Inside Post', 'Goal', 'Goal Far Post', 'Goal Inside Post']
xg_data['Event'] = pd.Categorical(xg_data['Event'], categories=custom_order, ordered=True)
xg_data = xg_data.sort_values('Event')

bolts_xg_data = xg_data.loc[xg_data['Team'].str.contains('Boston Bolts')]

dimensions = PitchDimensions(pitch_length_metres=100, pitch_width_metres=100)
fig1 = pfp.make_pitch_figure(
    dimensions,
    figure_height_pixels=800,
    figure_width_pixels=800
)

custom_order = ['Shot', 'Blocked', 'SOT', 'SOT Far Post', 'SOT Inside Post', 'Goal', 'Goal Far Post', 'Goal Inside Post']
xg_data['Event'] = pd.Categorical(xg_data['Event'], categories=custom_order, ordered=True)
xg_data = xg_data.sort_values('Event')

bolts_xg_data = xg_data.loc[xg_data['Team'].str.contains(selected_team)]

for index, row in bolts_xg_data.iterrows():
    x, y, xG = row['X'], 100-row['Y'], row['xG']
    hteam = row['Team']
    player_name = row['Player Full Name']
    url = row['Video Link']

    if row['Event'] == 'Goal':
        fig1.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers+text',
            marker=dict(
                size=(xG * 30) + 5,  # Adjusted for Plotly's scaling
                color='lightblue',
                symbol='circle'
            ),
            name='Goal',
            showlegend=False,
            hovertext=f"{player_name}<br>xG: {xG:.2f}",  # Add hover text
            hoverinfo="text"  # Display hover text
        ))
        fig1.add_annotation(
            x=x,
            y=y+3,
            text=f'<a href="{url}" target="_blank" style="color:lightblue;">Link</a>',
            showarrow=False,
            font=dict(color="lightblue"),
            align="center"
        ) 
    elif row['Event'] == 'SOT':
        fig1.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers',
            marker=dict(
                size=(xG * 30) + 5,
                color='white',
                line=dict(color='lightblue', width=3),
                symbol='circle'
            ),
            name='SOT',
            showlegend=False,
            hovertext=f"{player_name}<br>xG: {xG:.2f}",  # Add hover text
            hoverinfo="text"  # Display hover text
        ))
        fig1.add_annotation(
            x=x,
            y=y+3,
            text=f'<a href="{url}" target="_blank" style="color:lightblue;">Link</a>',
            showarrow=False,
            font=dict(color="lightblue"),
            align="center"
        ) 
    else:
        fig1.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers',
            marker=dict(
                size=(xG * 30) + 5,
                color='lightblue',
                symbol='circle-open'
            ),
            name='Shot',
            showlegend=False,
            hovertext=f"{player_name}<br>xG: {xG:.2f}",  # Add hover text
            hoverinfo="text"  # Display hover text
            ))
        fig1.add_annotation(
            x=x,
            y=y+3,
            text=f'<a href="{url}" target="_blank" style="color:lightblue;">Link</a>',
            showarrow=False,
            font=dict(color="white"),
            align="center"
        ) 
        
fig1.add_trace(go.Scatter(
    x=[None],  # Dummy data
    y=[None],
    mode='markers',
    marker=dict(
        size=10,
        color='lightblue',
        symbol='circle'
    ),
    name='Goal',
    visible='legendonly'
))

fig1.add_trace(go.Scatter(
    x=[None],  # Dummy data
    y=[None],
    mode='markers',
    marker=dict(
        size=10,
        color='white',
        line=dict(color='lightblue', width=3),
        symbol='circle'
    ),
    name='SOT',
    visible='legendonly'
))

fig1.add_trace(go.Scatter(
    x=[None],  # Dummy data
    y=[None],
    mode='markers',
    marker=dict(
        size=10,
        color='lightblue',
        symbol='circle-open'
    ),
    name='Shot',
    visible='legendonly',
))
        


custom_order = ['Shot', 'Blocked', 'SOT', 'SOT Far Post', 'SOT Inside Post', 'Goal', 'Goal Far Post', 'Goal Inside Post']
xg_data['Event'] = pd.Categorical(xg_data['Event'], categories=custom_order, ordered=True)
xg_data = xg_data.sort_values('Event')

opp_xg_data = xg_data.loc[~xg_data['Team'].str.contains(selected_team)]

for index, row in opp_xg_data.iterrows():
    x, y, xG, url = 100-row['X'], row['Y'], row['xG'], row['Video Link']

    ateam = row['Team']
    our_string = row['Event']
    if 'Goal' in our_string:
        fig1.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers+text',
            marker=dict(
                size=(xG * 30) + 5,  # Adjusted for Plotly's scaling
                color='red',
                symbol='circle'
            ),
            name='Goal Against',
            showlegend=False,
            hovertext=f"xG: {xG:.2f}",  # Add hover text
            hoverinfo="text"  # Display hover text
        ))
        fig1.add_annotation(
            x=x,
            y=y+3,
            text=f'<a href="{url}" target="_blank" style="color:red;">Link</a>',
            showarrow=False,
            font=dict(color="white"),
            align="center"
        ) 
    elif 'SOT' in our_string:
        fig1.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers',
            marker=dict(
                size=(xG * 30) + 5,
                color='white',
                line=dict(color='red', width=3),
                symbol='circle'
            ),
            name='SOT Against',
            showlegend=False,
            hovertext=f"xG: {xG:.2f}",  # Add hover text
            hoverinfo="text"  # Display hover text
        ))
        fig1.add_annotation(
            x=x,
            y=y+3,
            text=f'<a href="{url}" target="_blank" style="color:red;">Link</a>',
            showarrow=False,
            font=dict(color="white"),
            align="center"
        ) 
    else:
        fig1.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers',
            marker=dict(
                size=(xG * 30) + 5,
                color='red',
                symbol='circle-open'
            ),
            name='Shot Against',
            showlegend=False,
            hovertext=f"xG: {xG:.2f}",  # Add hover text
            hoverinfo="text"  # Display hover text
            ))
        fig1.add_annotation(
            x=x,
            y=y+3,
            text=f'<a href="{url}" target="_blank" style="color:red;">Link</a>',
            showarrow=False,
            font=dict(color="white"),
            align="center"
        ) 
        
# Add custom legend entries
fig1.add_trace(go.Scatter(
    x=[None],  # Dummy data
    y=[None],
    mode='markers',
    marker=dict(
        size=5,
        color='red',
        symbol='circle'
    ),
    name='Goal Against',
    visible='legendonly'
))

fig1.add_trace(go.Scatter(
    x=[None],  # Dummy data
    y=[None],
    mode='markers',
    marker=dict(
        size=5,
        color='white',
        line=dict(color='red', width=3),
        symbol='circle'
    ),
    name='SOT Against',
    visible='legendonly'
))

fig1.add_trace(go.Scatter(
    x=[None],  # Dummy data
    y=[None],
    mode='markers',
    marker=dict(
        size=5,
        color='red',
        symbol='circle-open'
    ),
    name='Shot Against',
    visible='legendonly',
))

fig1.update_layout(
    legend=dict(
        font=dict(
            size=8  # Decrease font size for smaller legend text
        ),
        itemsizing='constant',  # Keep marker sizes constant in the legend
        traceorder='normal'  # Keep the order of traces as added
    )
)

fig1.add_annotation(
    text="Click the top right of chart to see the shots better",
    x=0.5,
    y=1.13,  # Adjust this value to position the subtitle correctly
    xref="paper",
    yref="paper",
    showarrow=False,
    font=dict(
        size=14,
        family="Arial",
        color="gray"
    )
)

fig1.add_annotation(
    text = f"{selected_team} and {selected_opp} xG Shot Chart",
    y= 1.17,  # Vertical position of the title, 0.95 places it near the top
    x= 0.5,   # Horizontal position of the title, 0.5 centers it
    xref="paper",
    yref="paper",
    showarrow=False,
    font= dict(
        size= 18,
        family= 'Arial',
        color= 'black'
    )
)

st.plotly_chart(fig1)

st.session_state["selected_team"] = selected_team
st.session_state["selected_opp"] = selected_opp
st.session_state['selected_date'] = selected_date