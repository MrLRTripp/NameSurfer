# Import required libraries
import pandas as pd
from pathlib import Path
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import plotly.express as px

# Read the names data into pandas dataframe
# Create an empty DataFrame since the files don't have headers
def load_name_files():
    names_df = pd.DataFrame(columns=['State','Sex','Year','Name','NumOccurrences'])

    files_path = Path('E:/UserLo/source/repos/learning/Name Surfer/NamesByState')
    files_list = list (files_path.glob('*.txt'))
    for f in files_list:
        with f.open("r") as f_h:
            state_df = pd.read_csv(f_h,header=None,names=['State','Sex','Year','Name','NumOccurrences'])
            names_df=pd.concat([names_df,state_df],axis=0, copy=False)

    names_df = names_df.astype({'Year':'int32','NumOccurrences': 'int32'})


# Functions used to create name rank history DataFrame
def compute_name_occurences (df,states, sexes, years):
    """ df is the names DataFrame that has columns 
    ['State', 'Sex', 'Year', 'Name', 'NumOccurrences'], Year and NumOccurrences are int32
    states, sexes and years can be list, range, or set
    Note:
    Between 10% and 20% Male and Female names are the same so be aware when using both sexes
    """
    distinct_names = df[(df['State'].isin(states)) & (df['Sex'].isin(sexes)) & (df['Year'].isin(years))]['Name'].unique()

    name_occurrences_df = df[(df['State'].isin(states)) & (df['Sex'].isin(sexes)) & (df['Year'].isin(years)) & 
        (df['Name'].isin(distinct_names))].groupby(by=['Name']).sum()
    name_occurrences_df = name_occurrences_df.sort_values('NumOccurrences', ascending=False).reset_index()

    return name_occurrences_df[['Name','NumOccurrences']]

def compute_for_year_ranges(df,year_range,states='All', sexes = 'All'):
    """
    All the names with the same count will get the same rank. There are many names that have same count.
    df is the names DataFrame that has columns 
    ['State', 'Sex', 'Year', 'Name', 'NumOccurrences'], Year and NumOccurrences are int32

    year_range must be a range object 
    """
    # name_rank_year_ranges_df has index of all names. Columns = [Rank_<Year_range_1>,Rank_<Year_range_2>, Rank_<Year_range_3>, ...]
    name_rank_year_ranges_df = pd.DataFrame()   # Empty df to hold accumulated ranks

    if type(states) == str:
        if states == 'All':
            states = df['State'].unique()  # All the states
        else:
            states = [states] # Make individual state name a list

    if type(sexes) == str:
        if sexes == 'All':
            sexes = ['M','F']  # Both sexes
        else:
            sexes = [sexes] # Make individual sex a list

    # TODO: if year_range == 'All' then set range(1900,2020)

    for yr in year_range:
        # Each value of yr will be the start year of the sub_year_range.
        # yr+yr.step will be the stop year of the sub_year_range.
        # sub_year_range will have a step size of 1
        sub_year_range = range(yr,yr+year_range.step,1)

        # Find number of occurrences for a given name
        name_occurrences_df = compute_name_occurences (df,states, sexes, sub_year_range)
        count_num_occ = name_occurrences_df.groupby('NumOccurrences').count().sort_values('NumOccurrences',ascending=False).reset_index()

        # Compute rank for a given NumOccurrences. Then match name to number of occurrences
        # It makes sense to iterate using iterrows since the current_rank keeps accumulating
        # ['NumOccurrences','NumNames','Rank']
        # NumNames is the number of Names that have number of occurrences equal to NumOccurrences
        all_ranks_list = []
        current_rank = 1
        for idx, r in count_num_occ.iterrows():
            if idx != 0:
                current_rank += count_num_occ.loc[idx-1,'Name']

            all_ranks_list.append([r['NumOccurrences'], r['Name'],current_rank])
        all_ranks_df = pd.DataFrame(all_ranks_list,columns=['NumOccurrences','NumNames',f'{yr}'])

        # merge performs a database join of the type specified by how=
        # Set Name as the index to make it easier to get the rank using .loc
        # nameRank_df has index of all the names. Columns = [NumOccurrences,	NumNames,	Rank]
        nameRank_df = name_occurrences_df.merge(all_ranks_df, on='NumOccurrences',how='inner').set_index('Name')
        # Get just the Rank and merge it with name_rank_year_ranges_df
        merged_e_df = name_rank_year_ranges_df.merge(nameRank_df[[f'{yr}']],left_index=True, right_index=True,how='outer')
        merged_e_df.fillna(value=0, inplace=True)  # fillna is needed since names can appear and disappear over the years
        name_rank_year_ranges_df = merged_e_df
        

    return name_rank_year_ranges_df


# multi select for state, sex. Input box for Start, Stop, Step year. Do validation.
# Slider for year to animate Choropleth map of states. Try to find map that puts Alaska and Hawaii next to continental.

# Create a dash application
app = dash.Dash(__name__)

# Create an app layout
app.layout = html.Div(children=[html.H1('Name Surfer Dashboard',
                                        style={'textAlign': 'center', 'color': '#503D36',
                                               'font-size': 40}),
                                html.Br(),
                                'Based on ',
                                html.A('Stanford CS106A - Programming Methodology Name Surfer Assignment',href='https://see.stanford.edu/materials/icspmcs106a/39-assignment-6-name-surfer.pdf'),
                                html.Br(),
                                "The data is from ", 
                                html.A('SSA',href='https://www.ssa.gov/OACT/babynames/limits.html'),
                                # TASK 1: Add a dropdown list to enable Launch Site selection
                                # The default select value is for ALL sites
                                # dcc.Dropdown(id='site-dropdown',...)
                                #dcc.Dropdown(id='site_dropdown',
                                #options=
                                #    # Use a list comprehension to create the options
                                #    [{'label':elem, 'value':elem} for elem in launch_site_list]
                                #,
                                #value=launch_site_list[0],
                                #placeholder="Select a Launch Site",
                                #searchable=True
                                #),
                                html.Div(children=[
                                    html.Br(),
                                    html.Label('Sex'),
                                    dcc.Checklist(['Male', 'Female'],
                                                 ['Male', 'Female'],
                                                 id='sex'),

                                    html.Br(),
                                    html.Label('States'),
                                    dcc.Dropdown(['All','Alaska', 'Alabama', 'California'], 'All',multi=True, id='state'),
                                ], style={'padding': 10, 'flex': 1}),


                                html.Br(),

                                # TASK 2: Add a pie chart to show the total successful launches count for all sites
                                # If a specific launch site was selected, show the Success vs. Failed counts for the site
                                #html.Div(dcc.Graph(id='success-pie-chart')),
                                html.Br(),

                                html.P("Payload range (Kg):"),
                                ## TASK 3: Add a slider to select payload range
                                ##dcc.RangeSlider(id='payload-slider',...)
                                #dcc.RangeSlider(id='payload-slider',
                                #    min=0, max=10000, step=1000,
                                #    marks={0: '0',
                                #           2500: '2500',
                                #           5000:'5000',
                                #           7500:'7500',
                                #           10000:'10000'},
                                #    value=[min_payload, max_payload]),

                                # TASK 4: Add a scatter chart to show the correlation between payload and launch success
                                #html.Div(dcc.Graph(id='success-payload-scatter-chart')),
                                ])

# TASK 2:
# Add a callback function for `site-dropdown` as input, `success-pie-chart` as output
@app.callback(Output(component_id='success-pie-chart',component_property='figure'),
               Input(component_id='site_dropdown',component_property='value'))
def create_outcome_graph(launch_site_value):
    # Select data based on the launch_site_value
    if launch_site_value == launch_site_list[0]:
        selected_df = spacex_df.groupby('Launch Site',as_index=False).sum()
        fig = px.pie(selected_df, values='class', names='Launch Site',
             title=f'Total Booster Landing Success for {launch_site_value}')
    else:
        selected_df = pd.DataFrame(spacex_df[spacex_df['Launch Site']==launch_site_value]['class'].value_counts()).reset_index()
        selected_df.rename(columns={"index": "outcome", "class": "outcome_total"}, inplace=True)
        # Let's create a more meaningful outcome category to hold values "Success" or "Failure"
        selected_df["outcome_cat"] = selected_df["outcome"].astype("category")
        # 0 will map to first item in list, "Failure"
        # 1 will map to second item in list, "Success"
        selected_df["outcome_cat"].cat.categories= ["Failure", "Success"]
        fig = px.pie(selected_df, values='outcome_total', names='outcome_cat',
             title=f'Total Booster Landing Outcome for {launch_site_value}',
             color='outcome_cat',
             color_discrete_map={'Success':'green',
                                 'Failure':'red',})

    fig.update_traces(textposition='inside', textinfo='percent+label')

    return fig


# TASK 4:
# Add a callback function for `site-dropdown` and `payload-slider` as inputs, `success-payload-scatter-chart` as output
@app.callback(Output(component_id='success-payload-scatter-chart',component_property='figure'),
               Input(component_id='site_dropdown',component_property='value'),
               Input(component_id='payload-slider',component_property='value'))
def create_payload_graph(launch_site_value, payload_range):
    # Select data based on the launch_site_value
    if launch_site_value == launch_site_list[0]:
        selected_df = spacex_df[(spacex_df['Payload Mass (kg)'] >= payload_range[0]) & (spacex_df['Payload Mass (kg)']<=payload_range[1])]

        fig = px.scatter(selected_df, x='Payload Mass (kg)', y='class', color='Booster Version Category',
             title=f'Correlation between Payload and Success for {launch_site_value}')
    else:
        selected_df = spacex_df[(spacex_df['Payload Mass (kg)'] >= payload_range[0]) & (spacex_df['Payload Mass (kg)']<=payload_range[1]) \
            & (spacex_df['Launch Site']==launch_site_value)]

        fig = px.scatter(selected_df, x='Payload Mass (kg)', y='class', color='Booster Version Category',
             title=f'Correlation between Payload and Success for specific launch site {launch_site_value}')


    return fig


# Run the app
if __name__ == '__main__':
    app.run_server()
