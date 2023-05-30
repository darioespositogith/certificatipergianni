from dash import Dash, html, dcc, Input,Output,State, callback
from dash.exceptions import PreventUpdate
from dash.dash_table import *
from yahoo_fin.stock_info import *
import os
from pandas_ods_reader import read_ods
import pandas as pd
import datetime as dt

app = Dash(__name__)
server = app.server
content=pd.read_excel('assets/StartSet.xlsx')
content=content.fillna('')
titoli=['% Anno','ISIN Certificato','Prima Cedola','Ultima Cedola','Emittente','Nome Sottostante','Codice yahoo_fin Sottostante','Strike','Barriera','Mercato']
colonne=[{'id':name, 'name':name} for name in titoli],
content.columns=titoli 
print(content)
start_data=content.to_dict(orient='records')
                               
print(start_data)
app.layout=html.Div(children=[
                            dcc.Store(id='local', storage_type='local'),
                            html.H1('Certificati Gianni',style={'text-align':'center'}),
                            html.Div(children=[
                            html.Button(id='update_button',children='Aggiorna prezzi di mercato'),
                            html.Button(id='add_row',children='Aggiungi un rigo alla tabella')]),
                            dcc.Loading(DataTable(id='Tabella principale',
                                          data=start_data,
                                          #{name:'' for name in ['% Anno','ISIN Certificato','Prima Cedola','Ultima Cedola','Emittente','Nome Sottostante','Codice yahoo_fin Sottostante','Strike','Barriera','Mercato']}],
                                          style_data={
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'lineHeight': '15px'
                                            },                                   
                                          style_cell={'textAlign':'center','word-break':'break-all'},
                                            style_data_conditional=[
                                                {
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': 'rgb(220, 220, 220)',
                                                },
                                                {
                                                    'if': {'column_id': '% Anno'},
                                                    'backgroundColor': 'rgb(120, 120, 255)',
                                                }
                                            ],
                                          columns=[{'id':name, 'name':name} for name in titoli],
                                          page_size=30,
                                          filter_action="native",
                                          editable=True,
                                          sort_action="native",
                                          sort_mode="multi",
                                        ),
                type="circle",
                fullscreen=True)])

@callback(
    Output('Tabella principale', 'data'),
    Input('add_row', 'n_clicks'),
    State('Tabella principale', 'data'),
    State('Tabella principale', 'columns')
)
def add_row(n_clicks, rows, columns):
    if n_clicks:
        rows.append({c['id']: '' for c in columns})
    return rows

@callback(
    Output(component_id=f'Tabella principale', component_property='data',allow_duplicate=True),
    Input(component_id=f'update_button', component_property='n_clicks'),
    State(component_id=f'Tabella principale', component_property='data'),
    prevent_initial_call=True
)
def update_post_tables(click_to_update,old_data):
    if not click_to_update:
        raise PreventUpdate
    data=old_data
    if click_to_update > 0:
        print(f'old_data={old_data}')
        tickers=[line['Codice yahoo_fin Sottostante'].replace('\r','').upper() for line in old_data]
        print(f'tickers={tickers}')
        quotes={}
        for ticker in tickers:
            ticker=ticker.upper()
        for ticker in list(set(tickers)):
            quotes[ticker]=get_live_price(ticker)
        for line in old_data:
            line.update({'Mercato':quotes[line['Codice yahoo_fin Sottostante'].replace('\r','').upper()]})
        data=[line for line in old_data]
        print(f'new_data:{data}')
    return data

if __name__ == '__main__':
    app.run(port="1234", debug=False)