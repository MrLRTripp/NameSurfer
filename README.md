# NameSurfer and Name Choropleth

**Data Wrangling, Exploritory Data Analysis (EDA), and Data Visualization** using Python, Pandas, Numpy, Plotly, Dash

Inspired by NameSurfer assignment Stanford CS106A - Programming Methodology <https://see.stanford.edu/materials/icspmcs106a/39-assignment-6-name-surfer.pdf>

The data is from SSA <https://www.ssa.gov/OACT/babynames/limits.html>

Instead of using Java to create it, use Python and the graphics and dashboard tools.

There are two main files for NameSurfer: **namesurfer.ipynb** and **name_dash_app.py**. I prefer to use Jupyter Notebooks to develop/test/debug then move code to dash app where the graphs can be updated interactively.

**name_dash_app.py** can generate interesting graphs of first name populatity over time. They can also generate some interesting name statistics such as names with highest variance over time. See Screen Shots folder for some examples.

There are two main files for Name Choropleth: **name_choropleth.ipynb** and **name_choropleth_dash_app.py**. Again, the notebook is used for dev and testing of code before moving to the Dash app. The notebook is also used to generate the parquet file that is the DataFrame that has the reanking data in a format that can be quickly rendered in a choropleth. See screenshot of example choropleth. A fun thing to do is to use the slider to generate the progression of the name over the years.
