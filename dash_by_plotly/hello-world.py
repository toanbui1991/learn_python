from dash import Dash, dcc               # pip install dash
import dash_bootstrap_components as dbc  # pip install dash-bootstrap-components

#we have to know the concept of application layout, component and callback.
#
# Build your components
#define Dash application
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
#define markdown component
mytext = dcc.Markdown(children="# Hello World - let's build web apps in Python!")

# Customize your own Layout
#add component to layout
app.layout = dbc.Container([mytext])

# Run app
if __name__=='__main__':
    app.run_server(port=8051)