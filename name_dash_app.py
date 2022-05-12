# Import required libraries
import pandas as pd
from pathlib import Path
from dash import Dash, html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)


def load_name_files():
    """
    Read the names data into pandas dataframe
    Create an empty DataFrame since the files don't have headers
    """
    names_df = pd.DataFrame(
        columns=['State', 'Sex', 'Year', 'Name', 'NumOccurrences'])

    files_path = Path(
        'E:/UserLo/source/repos/learning/Name Surfer/NamesByState')
    files_list = list(files_path.glob('*.txt'))
    for f in files_list:
        with f.open("r") as f_h:
            state_df = pd.read_csv(f_h, header=None, names=[
                                   'State', 'Sex', 'Year', 'Name', 'NumOccurrences'])
            names_df = pd.concat([names_df, state_df], axis=0, copy=False)

    names_df = names_df.astype({'Year': 'int32', 'NumOccurrences': 'int32'})
    return names_df


# Functions used to create name rank history DataFrame
def compute_name_occurences(df, states, sexes, years):
    """ df is the names DataFrame that has columns 
    ['State', 'Sex', 'Year', 'Name', 'NumOccurrences'], Year and NumOccurrences are int32
    states, sexes and years can be list, range, or set
    Note:
    Between 10% and 20% Male and Female names are the same so be aware when using both sexes
    """
    distinct_names = df[(df['State'].isin(states)) & (
        df['Sex'].isin(sexes)) & (df['Year'].isin(years))]['Name'].unique()

    name_occurrences_df = df[(df['State'].isin(states)) & (df['Sex'].isin(sexes)) & (df['Year'].isin(years)) &
                             (df['Name'].isin(distinct_names))].groupby(by=['Name']).sum()
    name_occurrences_df = name_occurrences_df.sort_values(
        'NumOccurrences', ascending=False).reset_index()

    return name_occurrences_df[['Name', 'NumOccurrences']]


def compute_for_year_ranges(df, year_range, states, sexes):
    """
    All the names with the same count will get the same rank. There are many names that have same count.
    df is the names DataFrame that has columns 
    ['State', 'Sex', 'Year', 'Name', 'NumOccurrences'], Year and NumOccurrences are int32

    year_range must be a range object 
    """
    # name_rank_year_ranges_df has index of all names. Columns = [Rank_<Year_range_1>,Rank_<Year_range_2>, Rank_<Year_range_3>, ...]
    name_rank_year_ranges_df = pd.DataFrame()   # Empty df to hold accumulated ranks

    if states == ['All']:
        states = df['State'].unique()  # All the states in the input DataFrame

    # TODO: if year_range == 'All' then set range(1900,2020)

    for yr in year_range:
        # Each value of yr will be the start year of the sub_year_range.
        # yr+yr.step will be the stop year of the sub_year_range.
        # sub_year_range will have a step size of 1
        sub_year_range = range(yr, yr+year_range.step, 1)

        # Find number of occurrences for a given name
        name_occurrences_df = compute_name_occurences(
            df, states, sexes, sub_year_range)
        count_num_occ = name_occurrences_df.groupby('NumOccurrences').count(
        ).sort_values('NumOccurrences', ascending=False).reset_index()

        # Compute rank for a given NumOccurrences. Then match name to number of occurrences
        # It makes sense to iterate using iterrows since the current_rank keeps accumulating
        # ['NumOccurrences','NumNames','Rank']
        # NumNames is the number of Names that have number of occurrences equal to NumOccurrences
        all_ranks_list = []
        current_rank = 1
        for idx, r in count_num_occ.iterrows():
            if idx != 0:
                current_rank += count_num_occ.loc[idx-1, 'Name']

            all_ranks_list.append(
                [r['NumOccurrences'], r['Name'], current_rank])
        all_ranks_df = pd.DataFrame(all_ranks_list, columns=[
                                    'NumOccurrences', 'NumNames', f'{yr}'])

        # merge performs a database join of the type specified by how=
        # Set Name as the index to make it easier to get the rank using .loc
        # nameRank_df has index of all the names. Columns = [NumOccurrences,	NumNames,	Rank]
        nameRank_df = name_occurrences_df.merge(
            all_ranks_df, on='NumOccurrences', how='inner').set_index('Name')
        # Get just the Rank and merge it with name_rank_year_ranges_df
        merged_e_df = name_rank_year_ranges_df.merge(
            nameRank_df[[f'{yr}']], left_index=True, right_index=True, how='outer')

         # Don't replace NaN with 0. Plotly handles nan, by just skipping those values which is what we want.
        # merged_e_df.fillna(value=0, inplace=True)
        name_rank_year_ranges_df = merged_e_df

    return name_rank_year_ranges_df


# multi select for state, sex. Input box for Start, Stop, Step year. Do validation.
# Slider for year to animate Choropleth map of states. Try to find map that puts Alaska and Hawaii next to continental.
all_state_names_list = ['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','District of Columbia',
'Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine',
'Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada',
'New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon',
'Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia',
'Washington','West Virginia','Wisconsin','Wyoming']
all_state_abbrevations_list = ['AL','AK','AZ','AR','CA','CO','CT','DE','DC','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA',
'MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX',
'UT','VT','VA','WA','WV','WI','WY']
state_dict = dict(list(zip(all_state_names_list,all_state_abbrevations_list)))


# Read the data files
names_df = load_name_files()

# Create an app layout
app.layout = html.Div(children=[
    # dcc.Store stores all the name ranks
    dcc.Store(id='name-ranks'),

    html.H1('Name Surfer Dashboard'),
           # style={'textAlign': 'center', 'color': '#503D36',
           #        'font-size': 40, 'font-family': 'Arial, Helvetica, sans-serif'}),
    html.Br(),
    html.P(children=['Idea based on ',
                     html.A('Stanford CS106A - Programming Methodology Name Surfer Assignment',
                            href='https://see.stanford.edu/materials/icspmcs106a/39-assignment-6-name-surfer.pdf'),
                     ],
           ),
    html.P(children=["The data is from ",
                     html.A('SSA', href='https://www.ssa.gov/OACT/babynames/limits.html')],
           ),

    html.Div(children=[
        html.Label('Sex'),
        dcc.Checklist(['Male', 'Female'],
                      ['Male', 'Female'],
                      id='sex'),
        html.Br(),
        html.Label('States'),
        dcc.Dropdown(all_state_names_list, all_state_names_list, multi=True, id='states'),
    ], style={'padding': 10, 'flex': 1}),
    html.Div(children=[
        # Start year text box prepopulated with 1910
        html.Br(),
        html.Label('Enter Start Year'),
        dcc.Input(value='1910',
                  type='text', id='start-year'),
        # End  year text box prepopulated with 2010
        html.Br(),
        html.Label('Enter End Year', style={
            'padding-left': 20}),
        dcc.Input(value='2010',
                  type='text', id='end-year'),
        # Year step prepopulated with 5
        html.Br(),
        html.Label('Enter Year Step Size', style={
            'padding-left': 20}),
        dcc.Input(value='5', type='text',
                  id='year-step'),
        # Validate entries using call back
        html.Label('Fix dates',
                   id='date-validation',
                   style={'padding-left': 20,
                          'color': 'red',
                          'display': 'none'}
                   )

    ], style={'padding': 10, 'display': 'flex', 'flex-direction': 'row'}),

    html.Div(children=[
        # Refresh button after entering filter values
        # After button is clicked, read state of other components
        "After entering selection values, click to apply filters  ",
        html.Button('Apply Filters', id='apply-filters', n_clicks=0, className='button-primary')
    ] , style={'padding': 10, 'flex': 1}),

    html.Div(children=[
        # Check boxes of interesting names
        html.Label(
            'Select some interesting name groups'),
        dcc.Checklist(['Top 50 New Names', 'Most Variance', 'Presidents','First Ladies', 'The Beatles'],
                      ['The Beatles'],
                      id='interesting-names'),
        # Enter your own list of names. They will be added to the interesting names.
        html.Br(),
        html.Label(
            'Enter First Names Separated by Commas'),
        dcc.Input(placeholder='Enter Names...',
                  value='John,Paul,George,Ringo', type='text', id='csv-names'),

    ], style={'padding': 10, 'flex': 1}),

    html.Div(children=[
        # Refresh button after entering filter values
        # After button is clicked, read state of other components
        "After selecting names, click Refresh  ",
        html.Button('Refresh', id='refresh-val', n_clicks=0, className='button-primary')
    ] , style={'padding': 10, 'flex': 1}),

    # html.Br(),
    # html.Button('Shrink Width', id='shrink', n_clicks=0, className='button-primary'),
    # html.Br(),

    html.Div([
        dcc.Graph(id='name-rank-graph')
    ],id='graph-div',style={'width': '100%', 'display': 'inline-block', 'padding': '0 20'}),
    html.Div([
        html.P('No Data on these Names. Try different data filters.', style={'background-color':'yellow'}),
        html.Ul(id='missing-name-list'),
    ], id='missing', style={'display': 'none', 'width': '15%', 'float':'right'}),

    html.Br(),

])

# Validate date ranges. If not valid, add a red text message (make it visible).


#@app.callback(Output(component_id='date-validation', component_property='value'),
#              Input(component_id='start-year', component_property='value'),
#              Input(component_id='end-year', component_property='value'),
#              Input(component_id='year-step', component_property='value'))
#def validate_date(start, end, step):
#    return 1

def create_list_items(list):
    """
    Return a list of html.Li that will be set to children of html.Ul
    """
    result_li_items = [html.Li(item) for item in list]

    return result_li_items

TheBeatles = ['John','Paul','George','Ringo']
ThePresidents = ['George','John','Thomas','James','James','John','Andrew','Martin','William','John','James','Zachary',
'Millard','Franklin','James','Abraham','Andrew','Ulysses','Rutherford','James','Chester','Grover','Benjamin',
'William','Theodore','William','Woodrow','Warren','Calvin','Herbert','Franklin','Harry','Dwight','John',
'Lyndon','Richard','Gerald','Jimmy','Ronald','George','Bill','George','Barack','Donald','Joe']
TheFirstLadies = ['Jill','Abigail','Louisa','Ellen','Barbara','Laura','Rosalynn','Frances','Hillary','Grace','Mamie','Abigail',
'Betty','Lucretia','Julia','Florence','Anna','Caroline','Lucy','Lou','Rachel','Martha','Eliza','Lady',
'Jacqueline','Mary','Dolley','Ida','Elizabeth','Pat','Michelle','Jane','Sarah','Nancy','Edith','Eleanor',
'Helen','Margaret','Bess','Melania','Julia','Letitia','Hannah','Martha','Edith','Ellen']

# ['Top 50 New Names', 'Most Variance', 'Presidents','First Ladies', 'The Beatles']
def create_name_superset(n_set,interesting_names, result_df):
    super_set = set()
    for group in interesting_names:
        if group == 'The Beatles':
            super_set |= set(TheBeatles)
        elif group == 'Presidents':
            super_set |= set(ThePresidents)
        elif group == 'First Ladies':
            super_set |= set(TheFirstLadies)
        elif group == 'Most Variance':
            # Names with the greatest variance in rank over years
            # Exclude any names that dissappear, i.e. rank = NaN
            var_result_series = result_df[(result_df>=0).all(axis=1)].var(axis=1)
            var_result_top10_list = list(var_result_series.sort_values(ascending=False).head(10).index)
            super_set |= set(var_result_top10_list)
        elif group == 'Top 50 New Names':
            start_year = result_df.columns[0]
            end_year = result_df.columns[-1]
            series_start = result_df.loc[:,start_year]
            start_set=set(series_start[series_start>0].index)
            series_end = result_df.loc[:,end_year]
            end_set=set(series_end[series_end>0].index)
            new_name_list = list(end_set - start_set)
            # Sort ascending since lower values means higher rank
            top_50_new_names = list(result_df.loc[new_name_list].sort_values(by=end_year,ascending=True).head(50).index) 
            super_set |= set(top_50_new_names)

    return super_set | n_set





#@app.callback(
#    Output(component_id='graph-div', component_property='style'),
#    Output(component_id='missing', component_property='style'),
#    Output(component_id='missing-name-list', component_property='children'),
#    Input(component_id='shrink', component_property='n_clicks')
#)
#def show_missing_names(n_clicks):
#    if (n_clicks%2)==0:
#        return {'width': '100%', 'display': 'inline-block', 'padding': '0 20'},\
#               {'display': 'none', 'width': '15%', 'float':'right'},\
#               []
#    else:
#        # dynamically create list items
#        l = ['zazoo','zazam']
#        return {'width': '80%', 'display': 'inline-block', 'padding': '0 20'},\
#               {'display': 'inline-block', 'width': '15%', 'float':'right'},\
#               create_list_items(l)

# compute_for_year_ranges and the graphs generated after all the filters have been selected. Otherwise, some big dataframes will
# be created and thrown away until the final values are settled on.
# Use State to get the value of a component such as a text box, otherwise each individual character causes a callback
# State('input-on-submit', 'value')
# https://dash.plotly.com/dash-html-components/button
@app.callback(
    Output(component_id='name-ranks', component_property='data'),
    State(component_id='sex',component_property='value'),
    State(component_id='states',component_property='value'),
    State(component_id='start-year',component_property='value'),
    State(component_id='end-year',component_property='value'),
    State(component_id='year-step',component_property='value'),
    Input(component_id='apply-filters', component_property='n_clicks'), prevent_initial_call=True
)
def store_result_df(sex,states,start_year, end_year,year_step, n_clicks):
   if n_clicks is None:
       raise PreventUpdate
   else:
       # Call compute_for_year_ranges. Store the result df in JSON. When names change, read JSON an graph.
       yr_range = range(int(start_year),int(end_year), int(year_step))
       sex_1_char = [e[0] for e in sex]
       # The SSA data set uses 2-char state abbreviations, so look up abbreviation in state_dict
       state_abb_list = []
       for i in states:
            state_abb_list.append(state_dict[i])
       result_df = compute_for_year_ranges(names_df,yr_range,state_abb_list, sex_1_char)
       return result_df.to_json(date_format='iso', orient='split')


@app.callback(
    Output(component_id='name-rank-graph', component_property='figure'),
    Output(component_id='graph-div', component_property='style'),
    Output(component_id='missing', component_property='style'),
    Output(component_id='missing-name-list', component_property='children'),
    State(component_id='name-ranks', component_property='data'),
    State(component_id='csv-names', component_property='value'),
    State(component_id='interesting-names', component_property='value'),
    Input(component_id='refresh-val', component_property='n_clicks'), prevent_initial_call=True
)
def plot_name_ranks(name_ranks_json, csv_names,interesting_names,n_clicks):
    if name_ranks_json == None:
        raise PreventUpdate
    else:
        result_df = pd.read_json(name_ranks_json, orient='split')
        name_list = [e.strip() for e in csv_names.split(sep=',')] # strip whitespace
        n_set = set(name_list)
        # Create a superset of interesting names plus manually added names
        name_superset = create_name_superset(n_set,interesting_names, result_df)

        # Check the name_list to see which ones we have data on and which ones we don't
        set_r = set(result_df.index)
        clean = list(name_superset & set_r)
        missing = list(name_superset - set_r)
        if  (len(missing) > 0) and (missing[0]==''):
            missing.pop(0) # When all values are removed from text box, an empty string is returned so ignore it.

        if len(clean) > 0:
            result_df_t = result_df.loc[clean, :].T

            fig = px.line(result_df_t,x=result_df_t.index, y=result_df_t.columns) 
            fig.update_traces(mode='lines+markers')
            fig.update_yaxes(range=(result_df_t.max().max() + 1,.9))
            #  fig.update_yaxes(type='linear' if axis_type == 'Linear' else 'log')
            fig.update_xaxes(title_text="Years")
            fig.update_yaxes(title_text="Rank")
            fig.update_layout (legend_title_text='Names') 
            fig.update_layout (legend_title_font={'family':'Arial Black'}) 
        else: 
            fig = go.Figure() #empty figure

        if (len(missing) > 0):    
            return fig,\
                {'width': '80%', 'display': 'inline-block', 'padding': '0 20'},\
                {'display': 'inline-block', 'width': '15%', 'float':'right'},\
                create_list_items(missing)
        else:
            return fig,\
                {'width': '100%', 'display': 'inline-block', 'padding': '0 20'},\
                {'display': 'none', 'width': '15%', 'float':'right'},\
                []

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
