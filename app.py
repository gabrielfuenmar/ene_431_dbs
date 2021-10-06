# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 13:47:01 2021

@author: snf52211
"""


import pandas as pd
import geopandas as gpd
import glob

import dash
from dash import dash_table

from dash.dependencies import Input, Output
from dash import dcc
from dash import html

import plotly.graph_objs as go
import json
import pandas as pd
import numpy as np

import plotly.express as px
from sklearn import metrics
import os
import requests

files=[i for i in glob.glob('base_values\*')]

port=gpd.read_file("med_berths.geojson")

from_json = port.to_json()

geoJSON = json.loads(from_json)

MAPBOX_TOKEN=os.environ.get('MAPBOX_TOKEN', None)

def fig_update(val=0):
    
    df = pd.read_parquet(files[val])

    df=df.reset_index(drop=True)
    
    datamap=go.Data([go.Scattermapbox(
    mode = "markers+lines",
    lat = df.lat.tolist(),
    lon = df.lon.tolist(),marker=go.Marker(size=12,color="gray"),
    selected={'marker':{'color': 'black'}},
    hovertext=df["timestamp_position"])])

    layoutmap = go.Layout(
    height = 1500,
    autosize = True,
    showlegend = False,
    hovermode = 'closest',
    clickmode="event+select",
    geo = dict(
        projection = dict(type = "equirectangular"),
        ),
    mapbox = dict(layers=[
            dict(
                sourcetype = 'geojson',
                source = geoJSON ,
                type = 'fill',
                color = 'rgba(163,22,19,0.2)'
            )
        ],
        accesstoken = MAPBOX_TOKEN,
        center = dict(
            lat = df.lat.mean(),
            lon = df.lon.mean(),
            ),
        pitch = 0,
        zoom = 10,
        style = 'mapbox://styles/gabrielfuenmar/ckaocvlug34up1iqvowltgs5p'
    ),
    )
    
    fig=go.Figure(dict(data=datamap,layout=layoutmap))
    
    return fig

app = dash.Dash(__name__,
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
server=app.server

app.title="ENE 431 Anchoring selection"

app.layout = html.Div([dcc.Location(id='url', refresh=False),
    html.Div([html.Div([html.Div([html.Div(
        html.Button("Submit",id="submit-val",type="text"),
        className="three columns",style={ 'display': 'inline-block'}
    ),
        html.Div(
        html.Button("Previous",id="previous",type="text"),
        className="three columns",style={ 'display': 'inline-block'}
    ),
        html.Div(
        html.Button("Next",id="next",type="text"),
        className="three columns",style={ 'display': 'inline-block'}
    )]),
        html.Div(id="end",style={'left-margin': '15px'})],
                                 style={ 'display': 'flex',"flex-direction":"row","justify-content":"stretch"}),
                html.Div(dcc.Link(html.Button("Restart",id="restart",type="text"),href="/"))],
        style={ 'display': 'flex',"flex-direction":"row","justify-content":"space-between"},className="nine columns"),

    html.Div(html.H3(id="count")),
    html.Div(html.H4(id="score")),
    html.Div([html.Div([html.Div(className="three columns"),
                        html.Div(id="table_insert",className="three columns"),
                        html.Div(className="three columns")],
                        style={ 'display': 'flex',"flex-direction":"row","justify-content":"space-between"}),
              dcc.Graph(id='graph')],
        className="nine columns",
    ),
    ])


app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})


##Keep track class
class count:
    val=0
    one=0
    two=0
    three=0
    four=0
    def __init__(self,first=0,sec=0,third=0,fourth=0):
        self.one=first
        self.two=sec
        self.three=third
        self.four=fourth

db_res=count(first=0.89,sec=0.86,third=0.90,fourth=0.88)


def results(val):
    table_out=dash_table.DataTable(
                                id='table',
                                columns=[{"name": "Figure", "id": "Figure"},
                                         {"name": "Your result", "id": "Your result"},
                                         {"name": "M/L result", "id": "M/L result"}],
                                data=[{"Figure":"1","Your result":str(val.one),"M/L result":str(db_res.one)},
                                      {"Figure":"2","Your result":str(val.two),"M/L result":str(db_res.two)},
                                      {"Figure":"3","Your result":str(val.three),"M/L result":str(db_res.three)}],
                                style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                                style_cell={
                                'fontSize':20, 'font-family':'sans-serif',
                                'backgroundColor': 'rgb(50, 50, 50)',
                                'color': 'white'},
                            )
    return table_out


@app.callback(
    [Output('score', 'children'),
      Output('end', 'children')],
    [Input('graph', 'selectedData'),
      Input("submit-val", "n_clicks"),
      Input('next', 'n_clicks'),
      Input('previous', 'n_clicks'),
      Input("url","pathname")])

def score_update(selected,n_click,forw,back,path):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    
    if selected is not None and "submit-val" in changed_id:
        li = [item.get('pointIndex') for item in selected["points"]]
        df_in = pd.read_parquet(files[count.val])

        df_in=df_in.reset_index(drop=True)
        
        df_in=df_in.assign(input_value=np.where(df_in.index.isin(li),1,0))
        
        rand=metrics.cluster.adjusted_rand_score(df_in.marked_value, df_in.input_value)
        
        if count.val==0:
            count.one=round(rand,2)
        elif count.val==1:
            count.two=round(rand,2)
        elif count.val==2:
            count.three=round(rand,2)
        elif count.val==3:
            count.four=round(rand,2)
        
        text_r="Rand Index Score: {:.2f}".format(rand)
        
        if count.one!=0 and count.two!=0 and count.three!=0 and count.val==2:
            end_val=dcc.Link(html.Button("Results",type="text",id="result_button"),href='/results')
            
        else:
            end_val=None
    else:
        text_r=None
        end_val=None
       
    return text_r,end_val

         
@app.callback(
    [Output('graph', 'figure'),
     Output("table_insert","children"),
     Output('count', 'children'),],
    [Input('next', 'n_clicks'),
     Input('previous', 'n_clicks'),
     Input("url","pathname"),
     Input("restart","n_clicks")])

def click_update(ne,prev,path,res):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if "next" in changed_id:
        count.val=count.val+1
        
    elif "previous" in changed_id:    
        count.val=count.val-1
        
    elif "restart" in changed_id:
        count.val=0
    
    if count.val<=0:
        count.val=0
        
    if count.val>2:
        count.val=2
             
    fig_ex=fig_update(val=count.val)
    
    count_t="Figure {}".format(count.val+1)
    
    table=None

    if path=="/results":
        table=results(count)
        
        if count.val<2:
            table=None
                   
    return fig_ex,table,count_t
        
if __name__ == '__main__':
    app.run_server(debug=True)
    


