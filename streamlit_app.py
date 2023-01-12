import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
import plotly.offline as pyo

def filter_by_team_member(df, team_member):
    # Create a boolean mask to select only the rows where the "filter_column" is team_member
    mask = df['First Name'] == team_member

    # Use the mask to select only the rows that meet the condition
    filtered_df = df[mask]

    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(filtered_df, values='Hours', names='Project',title='Hours by Project for '+team_member, hole=0.4)
        fig.update_layout(height=400, width=400)
        fig.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=-1,
            bgcolor='rgba(0,0,0,0)'
        ))
        st.plotly_chart(fig)

    with col2:
        fig = px.pie(filtered_df, values='Hours', names='Task',title='Hours by Task for '+team_member, hole=0.4)
        fig.update_layout(height=400, width=400)
        fig.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=-1,
            bgcolor='rgba(0,0,0,0)'
        ))
        st.plotly_chart(fig)

    return

#define the working hours
st.markdown("**Calculates the median ticket response times**")
st.markdown("_The mean is used for normal number distributions, which have a low amount of outliers. The **median** is generally used to return the central tendency for skewed number distributions_")
sla_start_time = st.sidebar.slider("Start time for SLA",min_value=0,max_value=23)
sla_end_time = st.sidebar.slider("End time for SLA", min_value=sla_start_time+1, max_value=23)

see_tables = st.sidebar.checkbox("Show workings", value=False)
remove_weekends = st.sidebar.checkbox("Remove Sat & Sun", value=True)

# Read the Excel file into a pandas DataFrame
myfile = st.file_uploader("Select exported Teamwork Desk ticket file (.csv)")

if myfile != None:

    if st.button("Go!"):
        df = pd.read_csv(myfile)

        # Show the data as a table
        if see_tables: st.write(df)
        # create a list of the desired column names
        #cols_to_keep = ["CreatedAt", "Response Time (Minutes)", "Company", "Agent", "Tagged", "Customer"]
        cols_to_keep = ["CreatedAt", "Response Time (Minutes)", "Agent", "Tagged"]

        # create a new dataframe with only the desired columns
        df = df[cols_to_keep]
        #drop bad rows
        df.dropna(subset=['Response Time (Minutes)'], inplace=True)


        df['CreatedAt'] = df['CreatedAt'].str[:19]
        if see_tables:st.write(df)

        # convert the 'Datetime' column to a datetime object
        df['CreatedAt'] = pd.to_datetime(df['CreatedAt']) #, format='%Y-%m-%d %H:%M:%S'

        if remove_weekends: df = df[~(df['CreatedAt'].dt.dayofweek.isin([5,6]))]
        if see_tables:
            st.write("with weekends removed")
            st.write(df)

        # create a new column 'Time' and extract only the time information
        df['Time'] = df['CreatedAt'].dt.time
        if see_tables:st.write(df)

        df['Hour'] = df['CreatedAt'].dt.hour

        # create a new column with the period of the day
        #conditions = [
        #    (df['Hour'] >= 6) & (df['Hour'] < 12),
        #    (df['Hour'] >= 12) & (df['Hour'] < 18),
        #    (df['Hour'] >= 18) & (df['Hour'] <= 23) | (df['Hour'] < 6)
        #]
        #periods = ['Morning', 'Afternoon', 'Evening']
        #df['Period'] = np.select(conditions, periods, default='Night')

        conditions = [
            (df['Hour'] >= 0) & (df['Hour'] < sla_start_time),
            (df['Hour'] >= sla_start_time) & (df['Hour'] < sla_end_time),
            (df['Hour'] >= sla_end_time) & (df['Hour'] <= 23) | (df['Hour'] < sla_start_time)
        ]
        periods = ['Before SLA', 'SLA', 'After SLA']
        df['Period'] = np.select(conditions, periods, default='Night')

        if see_tables:st.write(df)

        median_response_time = df.groupby('Period')['Response Time (Minutes)'].median()
        sla_ticket_count = df.groupby('Period').size().reset_index(name='counts')
        if see_tables: st.write(median_response_time)
        if see_tables: st.write(sla_ticket_count)

        #total_count = sla_ticket_count['counts'].sum()
        #sla_ticket_count = sla_ticket_count.assign(Percentage=(sla_ticket_count['counts'] / total_count) * 100)
        #st.table(sla_ticket_count)


        st.header("Tickets by SLA")

        fig = px.pie(sla_ticket_count, values='counts', names='Period', title='SLA period is '+str(sla_start_time)+" to "+str(sla_end_time), hole=0.4)
        fig.update_layout(height=400, width=400)
        fig.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=-1,
            bgcolor='rgba(0,0,0,0)'
        ))
        st.plotly_chart(fig)


        # group the data by hour and count the occurrences
        data = df.groupby('Hour').size().reset_index(name='counts')
        median_data = df.groupby('Hour')['Response Time (Minutes)'].median().reset_index()
        if see_tables:st.write(data)
        if see_tables:st.write(median_data)

        total_count = sla_ticket_count['counts'].sum()
        data = data.assign(Percentage=(data['counts'] / total_count) * 100)


        st.header("Tickets by Hour")
        # create the bar chart
        bar = go.Bar(x=data['Hour'], y=data['counts'], name='counts')
        line = go.Scatter(x=median_data['Hour'], y=median_data['Response Time (Minutes)'], name='Response Time (Minutes)', yaxis='y2',mode='lines')

        # create the layout
        layout = go.Layout(title='Response Time by Hour of Day',
                           xaxis=dict(title='Hour'),
                           yaxis=dict(title='Count'),
                           yaxis2=dict(title='Median Response Time', overlaying='y', side='right'))

        # create the figure
        fig = go.Figure(data=[bar, line], layout=layout)

        st.plotly_chart(fig)
        st.table(data)
