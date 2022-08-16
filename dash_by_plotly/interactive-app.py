from dash import Dash, dcc, Output, Input  # pip install dash
import dash_bootstrap_components as dbc    # pip install dash-bootstrap-components

#Note: to understand the concept of call back we have to understant decorator and callback decorater.
#callback decorator have to get Input and Output object as parameters.
#then callback decorator will turn normal python function into a callback function.
#a callback functions is a function which in await status and be trigger with a event
# Build your components
app = Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])
mytext = dcc.Markdown(children='')
myinput = dbc.Input(value="# Hello World - let's build web apps in Python!")

# Customize your own Layout
app.layout = dbc.Container([mytext, myinput])

# Callback allows components to interact
#this callback function will take value from input and assign to child of Markdown
@app.callback(
    Output(mytext, component_property='children'),
    Input(myinput, component_property='value')
)
def update_title(user_input):  # function arguments come from the component property of the Input
    return user_input  # returned objects are assigned to the component property of the Output


# Run app
if __name__=='__main__':
    app.run_server(port=8052)