# If you prefer to run the code online instead of on your computer click:
# https://github.com/Coding-with-Adam/Dash-by-Plotly#execute-code-in-browser

from dash import Dash, dcc, Output, Input  # pip install dash
import dash_bootstrap_components as dbc    # pip install dash-bootstrap-components
import plotly.express as px
import pandas as pd                        # pip install pandas
import dash_mantine_components as dmc

# incorporate data into app
# Source - https://www.cdc.gov/nchs/pressroom/stats_of_the_states.htm
df = pd.read_csv("https://raw.githubusercontent.com/Coding-with-Adam/Dash-by-Plotly/master/Good_to_Know/Dash2.0/social_capital.csv")
print(df.head())

# Build your components
app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])
mytitle = dcc.Markdown(children='')
mygraph = dcc.Graph(figure={})
dropdown = dcc.Dropdown(options=df.columns.values[2:],
                        value='Cesarean Delivery Rate',  # initial value displayed when page first loads
                        clearable=False)
myalert = dmc.Alert(children="Scatter plot is not the best graph for these data!")

# Customize your own Layout
# container will take a list of objects. in this case we define container as list of Row.
#  Row also take a list of object. in this case Row take Col, specify row justified is center
# Col take a list of objects in this case it take component object and specified the with of col 
# app.layout = dbc.Container([
#     dbc.Row([
#         dbc.Col([mytitle], width=6)
#     ], justify='center'),
#     #excercise one: change layout
#     dbc.Row([
#         dbc.Col([mygraph], width=8), 
#         dbc.Col([dropdown], width=4)
#     ])

# ], fluid=True)
#excercise 4
app.layout = dbc.Container([mytitle, myalert, mygraph, dropdown])

# Callback allows components to interact
# callback decorator with multiple output and input
# we have two outputs therefore we needs to return two object
@app.callback(
    Output(mygraph, 'figure'),
    Output(mytitle, 'children'),
    Input(dropdown, 'value')
)
def update_graph(user_input):  # function arguments come from the component property of the Input
    if user_input == 'Bar Plot':
        fig = px.bar(data_frame=df, x="nation", y="count", color="medal")
        alert_text = "The data for the bar graph is highly confidential."

    elif user_input == 'Scatter Plot':
        fig = px.scatter(data_frame=df, x="count", y="nation", color="medal",
                         symbol="medal")
        alert_text = "The scatter plot is believed to have been first published in 1833."

    return fig, alert_text # returned objects are assigned to the component property of the Ouput
# def update_graph(column_name):  # function arguments come from the component property of the Input

#     print(column_name)
#     print(type(column_name))
#     # https://plotly.com/python/choropleth-maps/
#     # fig = px.choropleth(data_frame=df,
#     #                     locations='STATE',
#     #                     locationmode="USA-states",
#     #                     scope="usa",
#     #                     height=600,
#     #                     color=column_name,
#     #                     animation_frame='YEAR')
#     # excercise 2
#     # https://plotly.com/python/bar-charts/
#     # fig = px.bar(data_frame=df, x='STATE', y=column_name)
#     # excercise 3
#     # https://plotly.com/python/line-charts/
#     fig = px.line(data_frame=df, x='YEAR', y=column_name, color='STATE')

#     return fig, '# '+column_name  # returned objects are assigned to the component property of the Output


# Run app
if __name__=='__main__':
    app.run_server(debug=True, port=8054)