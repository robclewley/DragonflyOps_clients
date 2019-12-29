import dash
import dash_html_components as html
import dash_core_components as dcc
import chart_studio.plotly as py
import plotly.graph_objs as go
from dash.dependencies import Input, Output

import time
import pandas as pd
import numpy as np
import seaborn as sns
import json
import ast

from test_diagnostics import *

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',
                        'static/css/dash_config.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = False

# ==========================

units = ast.literal_eval(attr('level.map_obj.units'))
connxns = ast.literal_eval(attr('level.map_obj.connxns'))
connected_str = attr('level.map_obj.connected_to')
ix1 = connected_str.index('{')
ix2 = connected_str.index('}')+1
connected_to = ast.literal_eval(connected_str[ix1:ix2])
sectors = get_json(attr('level.sectors_obj.sectors'))
xdim = max(u[0] for u in units)
ydim = max(u[1] for u in units)

cols = sns.color_palette("muted", len(sectors))
map_data = []

for (x,y), cx_list in connected_to.items():
    #xs, ys = zip(*cx_list)
    for x1, y1 in cx_list:
        line = go.Scattergl(x=[x,x1],
                       y=[ydim-y,ydim-y1],
                       mode='lines',
                       showlegend=False,
                       line=dict(width=4, color='Black'))
        map_data.append(line)


for i, (sec_name, sec_units) in enumerate(sectors.items()):
    xs, ys = zip(*sec_units)
    locs = go.Scattergl(x=xs,
                      y=[ydim-y1 for y1 in ys],
                      mode='markers',
                      name=sec_name,
                      marker=dict(
                                  color='rgb({},{},{})'.format(*cols[i]),
                                  size=20,
                                  line=dict(width=3, color='DarkSlateGrey')
                                  ),
                      )
    map_data.append(locs)

# ================

scale = 50

class StateHolder(object):
    def __init__(self):
        self.play_pressed = False

    def get_state(self):
        if self.play_pressed:
            s = {}
            #print(attr('player.pos'))
            s['player_pos'] = ast.literal_eval(attr('player.pos'))
            #print(s)
            return s
        else:
            #time.sleep(0.3)
            return

S = StateHolder()

layout = go.Layout(
    xaxis=dict(
        #showticklabels=False,
        showgrid=False,
        zeroline=False,
        autorange=False,
        range=[-1, xdim+1],
    ),
    yaxis=dict(
        #showticklabels=False,
        showgrid=False,
        zeroline=False,
        autorange=False,
        range=[-1, ydim+1],
        tickmode = 'array',
        tickvals = ydim-np.arange(ydim+1),
        ticktext = [str(yval) for yval in np.arange(ydim+1)]
    ),
    margin={
        'l': 50,
        'r': 10,
        't': 10,
        'b': 10
    },
    height=int(ydim*scale),
    width=int(xdim*scale*1.15),
    #uirevision=0 # never refresh UI state (keep value constant)
)


fig = go.Figure(data=map_data, layout=layout)

app.layout = html.Div(
    html.Div([
        html.H4('Live map'),
        html.Div(id='live-update-text'),
        html.Button('Start', id='button'),
        dcc.Graph(id='live-update-graph',
                  figure=fig,
                  config={
                      'displayModeBar': False,
                    'modeBarButtonsToRemove': ['autoScale2d', 'select2d', 'zoom2d',
                                               'pan2d', 'toggleSpikelines',
                                               'hoverCompareCartesian',
                                               'zoomOut2d', 'zoomIn2d',
                                               'hoverClosestCartesian',
                                               'lasso2d',
                                               # 'sendDataToCloud',
                                               'resetScale2d']
                    }),
        html.Div(id='hidden-div', style={'display':'none'}),
        dcc.Interval(
            id='interval-component',
            interval=2000, #int(dt*1000), # in milliseconds  WON'T SHOW IF TOO FAST
            n_intervals=0
        )
    ])
)



@app.callback(Output('live-update-text', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_text(n):
    #s = S.get_state()
    style = {'padding': '5px', 'fontSize': '16px'}
    return [html.Span('TEST', style=style),
            html.Span('STUFF', style=style)]

@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    s = S.get_state()
    if s is None:
        data = []
    else:
        player = go.Scatter(x=[s['player_pos'][0]],
                       y=[ydim-s['player_pos'][1]],
                       mode='markers',
                       name='player',
                       marker=dict(
                                   color='Black',
                                   size=30,
                                   symbol='diamond'
                                   )
                       )
        data = [player]
    return go.Figure(data=data+map_data, layout=layout)

@app.callback(Output('hidden-div', 'children'),
              [Input('button', 'n_clicks')])
def start(n):
    if n is not None and n >= 1:
        S.play_pressed = True

if __name__ == '__main__':
    app.run_server(debug=True)

