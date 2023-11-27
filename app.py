import os
from dash import Dash, html, dcc, Output, Input, State
import dash_cytoscape as cyto
import pandas as pd
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
import numpy as np
from flask import Flask

# flask_server = Flask(__name__)
app = Dash(__name__) # server=flask_server)
# server = app.server

graph_style = [
            {
                'selector': 'node',
                'style': {
                    'label': 'data(label)'
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'line-color': 'green'
                }
            },
            {
                'selector': '.primary-movie',
                'style': {
                    'background-color': 'red',
                }
            },
            {
                'selector': '.secondary-movie',
                'style': {
                    'background-color': 'yellow',
                }
            },
            {
                'selector': '.person',
                'style': {
                    'background-color': 'blue',
                }
            }
        ]

# graph = cyto.Cytoscape(
#         # id='cytoscape-two-nodes',
#         layout={
#             'name': 'cose'
#         },
#         style={'width': '100%', 'height': '90vh'},
#         elements=[
#             {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 75, 'y': 75}},
#             {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 200, 'y': 200}},
#             {'data': {'source': 'one', 'target': 'two'}}
#         ],
#         stylesheet=graph_style
#     )


titles = pd.read_csv("titles.csv")
titles["primaryTitle"].fillna("", inplace=True)
titles["originalTitle"].fillna("", inplace=True)


# people_reduced = pd.read_csv("people_reduced.csv")
# people_reduced["primaryProfession"].fillna("", inplace=True)

principals = pd.read_csv("principals.csv")


center_style = {"width": "100vw", "display": "flex", "align-items": "center", "height": "50vh", "justify-content": "center"}


app.layout = html.Div([
    dmc.Stack([
        dmc.Grid(
            children=[
                dmc.Col(dmc.TextInput(label="Search a Movie Title", id='search-field'), span=3),
                dmc.Col(dmc.MultiSelect(
                    label="Select Roles",
                    placeholder="Select all you like!",
                    id="role-select",
                    value=["director"],
                    data=[
                        {"value": "actor", "label": "actor/actress"},
                        {"value": "director", "label": "director"},
                        {"value": "writer", "label": "writer"},
                    ]
                ), span=4),
                dmc.Col(dmc.Button('Search', id='search-button'), span="content"),
            ],
            align="flex-end",
            justify="center",
            style={"height": "10vh"}
        ),
        html.Div([
            html.Div("Start Searching For Movies.", className="center-container")
        ], id="graph-container", className="graph-container")
    ], style={"height": "100vh"}),
])

# callback to update graph
@app.callback(
    Output('graph-container', 'children'),
    Input('search-button', 'n_clicks'),
    State('search-field', 'value'),
    State('role-select', 'value'))
def update_graph(n_clicks:int, search_string:str, roles:list[str]):
    if n_clicks:
        # print(roles)

        search_result = titles.loc[titles['originalTitle'] == search_string].to_dict('records')

        if len(search_result) == 0:
            return html.Div("No results found.", className="center-container")
        elif len(search_result) > 1:
            raise ValueError("Too many results found")

        title_id = search_result[0]["tconst"]
        # print(title_id)

        people_res = principals.loc[(principals.tconst == title_id) & (principals.category.isin(roles))]
        people_res_dict = people_res.to_dict('records')

        nodes = [
                {'data': {'id': i["primaryTitle"], 'label': f'{i["primaryTitle"]} ({i["startYear"]})'}, "classes": "primary-movie"} for i in search_result
            ]
        
        print(people_res)

        edges = []

        for person in people_res_dict:
            nodes.append({'data': {'id': person["primaryName"], 'label': person["primaryName"]}, "classes": "person"})
            edges.append({'data': {'source': person["primaryName"], 'target': search_result[0]["primaryTitle"]}})

            associated_with = principals.loc[person["nconst"] == principals["nconst"], "tconst"]
            associated_titles = titles.merge(associated_with, left_on="tconst", right_on="tconst").to_dict("records")

            print(list(associated_with))

            nodes += [{'data': {'id': i["primaryTitle"], 'label': i["primaryTitle"] + f" ({i['startYear']})"}, "classes": "secondary-movie"} for i in associated_titles if i["primaryTitle"] != search_string]
            edges += [{'data': {'source': person["primaryName"], 'target': i["primaryTitle"]}} for i in associated_titles if i["primaryTitle"] != search_string]

        print(nodes)
            # print(associated_with)

        graph = cyto.Cytoscape(
            layout={
                'name': 'cose'
            },
            style={'width': '100%', 'height': '900px'},
            className="graph",
            elements = nodes + edges,
            stylesheet=graph_style
        )


        return [graph]
    else:
        raise PreventUpdate


if __name__ == "__main__":
    # Get port and debug mode from environment variables
    port = os.environ.get('dash_port', 8050)
    debug = os.environ.get('dash_debug')=="True"
    app.run_server(debug=debug, host="0.0.0.0", port=port)