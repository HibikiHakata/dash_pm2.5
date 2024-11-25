# データ分析関連のライブラリ
import pandas as pd

# dash関連のライブラリインポート
import dash  
from dash import dash_table
import dash_uploader as du
import dash_bootstrap_components as dbc
from dash import dcc 
from dash import html  
from dash.dependencies import Input, Output
import plotly.express as px

# 季節性補正倍率のデータを読み込み
path = "スクリプト/dash_test/data/seasonal_ratio.csv"
df_season_ratio = pd.read_csv(path)

df_pt = (
    df_season_ratio
    .assign(
    季節性補正倍率=lambda df: 
    round(df['季節性補正倍率'], 2)
    )
    .pivot_table(
        index=['月'], 
        columns=['商品ファミリー名称_発売年月'], 
        values=['季節性補正倍率']
        )
    .reset_index(drop=True)
    .droplevel(0, axis=1)
)
df_pt.index.name = None

df_pt_show = df_pt.T.reset_index()
df_pt_show.columns = ['商品ファミリー名称_発売年月'] + [(str(j+1) + '月') for j in range(12)]

items_list = list(df_pt.T.index.unique())
items_label = [item.split("_")[0].strip("CPB ") for item in items_list]
items_dict = {k: v for k, v in zip(items_label, items_list)}
options = [{"label":k, "value":v} for k, v in items_dict.items()]

# appという箱作り①
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

sidebar = html.Div([html.H3("sidebar"), html.H3("sidebar")],
                   hidden=False, id="sidebar", className="w3-sidebar w3-bar-block",
                   style={"width": "25%", "background-color": "#EEEEEE"})

content = html.Div(
    [
        dbc.Row(
            html.Div(
                [
                    html.H1('Seasonal_Ratio'),
                    dcc.Graph(
                        id = "first-graph",
                        figure = {
                        'data': [
                            {'x': (df_pt.index + 1),
                            'y':df_pt['CBP ﾙｾﾗﾑ30_201908'],
                            'type': 'plot',
                            'name': 'CBP ﾙｾﾗﾑ30_201908'},
                            {'x':(df_pt.index + 1),
                            'y':df_pt['CPB エマルション アンタンシブ_201908'],
                            'type': 'plot',
                            'name': 'CPB エマルション アンタンシブ_201908'}
                        ],
                        'layout': {
                            'title': 'サマリマスタ名称別_季節性補正倍率'}
                        }
                    )
                ]
            )
        ),
        dbc.Row([
                    html.H1("Dash app with export dataset"),
                    dcc.Dropdown(
                        id='my-dropdown',
                        options=options,
                        value='CBP ﾙｾﾗﾑ30_201908'
                    ),
                    html.Div(id='output-container', style={"margin": "5%"})
                ]
        )
    ]
)

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(sidebar, width=2, className='bg-light'),
                dbc.Col(content, width=8)
                ],
            style={"height": "100vh"}
            ),
        ],
    fluid=True
    )

@app.callback(
    Output('output-container', 'children'),
    [Input('my-dropdown', 'value')]
)
def input_triggers_spinner(value):
    df_filtered = df_pt_show[df_pt_show["商品ファミリー名称_発売年月"] == value]
    
    output_table = dash_table.DataTable(
        id='table',
        data=df_filtered.to_dict('records'),        
        columns= [{"name": i, "id": i} for i in df_pt_show.columns],
        editable=True,
        export_format='csv',
    )
    return output_table

# 実行用③
if __name__=='__main__':
    app.run_server(debug=True, port=1234)
