import pandas as pd
import glob
import os
import streamlit as st

def UpdatingActions():
    # Path to the folder containing CSV action files
    folder_path = 'Bolts-SS/WeeklyReport PSD'

    allowable_teams = ['Boston Bolts U13 NALSS', 'Boston Bolts U14 NALSS']

    # Find all CSV files in the folder
    csv_files = glob.glob(os.path.join(folder_path, '*.csv'))

    # List to hold individual DataFrames
    df_list = []

    # Loop through the CSV action files and read them into DataFrames
    for file in csv_files:
        df = pd.read_csv(file)
        df.columns = df.iloc[3]
        df = df.iloc[4:]
        df = df.reset_index(drop=True)

        start_index = df.index[df["Period Name"] == "Round By Position Player"][0]

        # Find the index where "period name" is equal to "running by position player"
        end_index = df.index[df["Period Name"] == "Round By Team"][0]

        # Select the rows between the two indices
        selected_rows = df.iloc[start_index:end_index]

        # Reset the index (optional if you want a clean integer index)
        selected = selected_rows.reset_index(drop=True)
        # selecting appropriate columns
        selected = selected[['Team Name', 'Match Date', 'Opposition']]
        if selected['Team Name'].isin(allowable_teams).any():
            # Append only the filtered DataFrame to the list
            df_list.append(selected)

    # Concatenate all DataFrames into a single DataFrame
    combined_df = pd.concat(df_list, ignore_index=True)
    return combined_df


