# 開発メモ
'''
ウィンドウを4つに分割し、右2つに現在のインタラクティブなグラフ操作環境を配置する
左上には美類分類×シーズンごとの季節性グラフを配置したい
左下には、season_ratioのRawデータを配置したい
全商品のデータをページ送りで見ることができるようにして、exportボタンでデータをダウンロードできるように
'''

# Import libraries
from dash import Dash, dash_table, dcc, Input, Output, State, html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# 季節性補正倍率のデータを読み込み
path = "スクリプト/dash_test/data/season_ratio.csv"
df_season_ratio = (
    pd.read_csv(path)
    .assign(
    倍率復元用_季節性合計値=lambda df: 
    round(df['倍率復元用_季節性合計値'], 2)
    )
)

# TODO:この部分いらないので、あとで編集する
df_pt = (
    df_season_ratio
    .assign(
    季節性補正倍率_標準化=lambda df: 
    round(df['季節性補正倍率_標準化'], 2)
    )
    .pivot_table(
        index=['月'], 
        columns=['商品ファミリー名称_発売年月'], 
        values=['季節性補正倍率_標準化']
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
# ここまでいらない


# Create a Dash DataTable
data_table = html.Div(id='output-container', style={"margin": "5%"})
data_table_2 = html.Div(
    dash_table.DataTable(
        data=df_season_ratio.to_dict('records'),
        columns=[{'name': i, 'id': i,'selectable':True} for i in df_season_ratio.columns],
        page_size=12,
        column_selectable="multi",
        selected_columns=['季節性補正倍率_標準化'],
        export_format='xlsx',
        sort_action='native',
        filter_action='native'
        ),
    id='output-container2',
    style={"margin": "5%"}
)

# Create a line graph of life expectancy over time
fig = px.line(df_season_ratio, x='月', y='季節性補正倍率_標準化', color='商品ファミリー名称_発売年月', markers=True)
graph1 = dcc.Graph(id='figure1', figure=fig)

item_selector = dcc.Dropdown(
                        id='my-dropdown',
                        options=options,
                        value=options[0]["value"]
                    )

# Create the Dash application with Bootstrap CSS stylesheet
app = Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP], 
    suppress_callback_exceptions=True
)

# Create the app layout
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col([
                    data_table,
                    item_selector
                ],
                width=4
                ),
                dbc.Col([
                    html.Div([
                        html.Button(id='submit-button', children='Submit')
                    ])
                ],
                width=1
                ),        
                dbc.Col([
                    graph1
                ],
                width=7
                )
            ],
            style={"height": "55vh"}
        ),
        dbc.Row(
            [
                # dbc.Col(html.Div(''), width=2),
                dbc.Col([
                    html.H2("現在登録されている季節性補正倍率"),            
                    data_table_2
                ],
                width=8
                ),
                dbc.Col(html.Div(''), width=2)
            ],
            style={"height": "45vh"}        
            )
    ],
    fluid=True
)


@app.callback(
    Output('output-container', 'children'),
    [Input('my-dropdown', 'value')]
)
def input_triggers_spinner(value):
    df_filtered = df_season_ratio[df_season_ratio["商品ファミリー名称_発売年月"] == value]
    
    output_table = dash_table.DataTable(
        id='dataTable1', 
        data=df_filtered.to_dict('records'), 
        columns=[{'name': i, 'id': i,'selectable':True} for i in df_season_ratio.columns],
        page_size=12,
        column_selectable="multi",
        selected_columns=['季節性補正倍率_標準化'],
        editable=True
    )
    return output_table



# Link DataTable edits to the plot with a callback function
@app.callback(
    Output('figure1', 'figure'),
    [
        Input('dataTable1', 'data'),
        Input('dataTable1', 'columns'),
        Input('dataTable1', 'selected_columns')
    ]
)
def display_output(rows, columns, sel_col):
    # Create data frame from data table 
    df = pd.DataFrame(rows, columns=[c['name'] for c in columns])
    # Create a new figure to replace previous figure
    fig = px.line(df, x='月', y=sel_col[0], color='商品ファミリー名称_発売年月', markers=True)
    fig.add_hline(y=1)
    return fig



@app.callback(
    Output('output-container2', 'children'),
    [
        Input('submit-button','n_clicks'),
    ],
    [   
        State('my-dropdown','value'),
        State('dataTable1', 'data'),        
        State('dataTable1', 'columns')
    ]
)
def update_datatable(value, n_clicks, rows, columns):
    global df_season_ratio
    global updated_table
    
    if n_clicks:
        df_item_updated = pd.DataFrame(rows, columns=[c['name'] for c in columns])
        df_base = df_season_ratio.query("商品ファミリー名称_発売年月 != @value")

        df_season_ratio = (
            pd.concat(
                [
                df_base,
                df_item_updated
                ], axis=0)
            .sort_values(["商品ファミリー名称_発売年月", "月"])
            )
        # # df_season_ratio.loc[df_season_ratio['商品ファミリー名称_発売年月'] == value, '季節性補正倍率_標準化'] = df_item_updated['季節性補正倍率_標準化']
        updated_table = dash_table.DataTable(
        id='dataTable2',
        data=df_season_ratio.to_dict('records'), 
        columns=[{'name': i, 'id': i} for i in df_season_ratio.columns],
        page_size=12,
        export_format='xlsx',
        sort_action='native',
        filter_action='native'
        )
        return updated_table
    else:
        updated_table = df_season_ratio
        return updated_table

# Launch the app server
if __name__ == '__main__':
    app.run_server(debug=True, port=1234)
