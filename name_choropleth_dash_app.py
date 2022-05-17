# Import required libraries
import pandas as pd
from pathlib import Path
from dash import Dash, html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

# Load the state names result parquet file
files_path = 'E:/UserLo/source/repos/learning/Name Surfer/'
result_parquet_file = "result_all_states_all_names_1910_2020_5.parquet"
result_parquet_df=pd.read_parquet(files_path+result_parquet_file)

def gen_choropleth_for_name_year(result_df,name,year):
    """
    gen_choropleth_for_name_year
    Using the previously computed state names result DataFrame, generate a choropleth map of USA states showing the ranking by state.

    Return:
    Plotly Graph Objects Figure
    """
    if type(year)!=str:
        year = f'{year:4.0f}'
    color_max = result_df.xs(name, level=("names"), axis=0).max().max()
    color_max = min(color_max, 500)
    color_min = result_df.xs(name, level=("names"), axis=0).min().min()
    fig = go.Figure(data=go.Choropleth(
        locations=list(result_df.xs(name, level=("names"), axis=0).index), # Spatial coordinates
        z = result_df.xs(name, level=("names"), axis=0).loc[:,year], # Data to be color-coded

        # The built-in Plotly geojson for USA is lower resolution, but much faster to render than states_geojson_clean_dict
        # If you want to switch, comment out locationmode and uncomment geojson and featureidkey
        locationmode = 'USA-states', # set of locations match entries in `locations`
        #geojson=states_geojson_clean_dict, 
        #featureidkey="properties.Abbreviation",

        colorscale = 'Viridis',
        reversescale=True,
        zmin=color_min, zmax = color_max,
        colorbar=dict(title='Name Popularity Rank',
        )
    ))

    fig.update_layout(
        geo_scope='usa', # limit map scope to USA
        title_text = f'{year} Popularity Rank for {name} by State')

    # fig.update_coloraxes(colorbar=dict(orientation='h'))


    return fig


# Create an app layout.
# 
app.layout = html.Div(children=[
    html.H1('United States Name Rankings'),
    html.H4('Show popularity of name by state'),
           # style={'textAlign': 'center', 'color': '#503D36',
           #        'font-size': 40, 'font-family': 'Arial, Helvetica, sans-serif'}),
    html.Br(),
    html.P(children=['Builds upon idea inspired by ',
                     html.A('Stanford CS106A - Programming Methodology Name Surfer Assignment',
                            href='https://see.stanford.edu/materials/icspmcs106a/39-assignment-6-name-surfer.pdf'),
                     ],
           ),
    html.P(children=["The data is from ",
                     html.A('SSA', href='https://www.ssa.gov/OACT/babynames/limits.html')],
           ),
    html.Div(children=[
        html.Label(
            'Enter First Name '),
        dcc.Input(placeholder='Enter Name...',
                  value='John', type='text', id='first-name'),

    ], style={'padding': 10, 'flex': 1}),

    html.Div([
        dcc.Graph(id='name-choropleth')
    ],id='graph-div',style={'padding': '0 20'}),
    html.Div([
        dcc.Slider(1910, 2015, 5,
               value=1910,
               marks={i: f'{i:4d}' for i in range(1910, 2020, 5)},
               updatemode='drag',
               id='year-slider'
        ),
        html.Div(["Select year to display"], style={'padding': 10, 'flex': 1})

    ]),

    html.Br(),

])

@app.callback(
    Output(component_id='name-choropleth', component_property='figure'),
    State(component_id='first-name', component_property='value'),
    Input(component_id='year-slider', component_property='value')
)
def plot_choropleth(name, year):

    return gen_choropleth_for_name_year(result_parquet_df,name,year)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
