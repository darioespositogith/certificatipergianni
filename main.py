from dash import Dash, html, dcc, Input,Output,State, callback
from dash.exceptions import PreventUpdate
from dash.dash_table import *
from dash.dash_table.Format import Format, Scheme, Group, Symbol
from yahoo_fin.stock_info import *
import os
import logging
#from apscheduler.schedulers.background import BackgroundScheduler
#from pandas_ods_reader import read_ods
import pandas as pd
#import datetime as dt

euroformat=Format(scheme=Scheme.fixed, 
                precision=2,
                group=Group.yes,
                groups=3,
                group_delimiter='.',
                decimal_delimiter=',',
                symbol=Symbol.yes, 
                symbol_prefix=u'€')

app = Dash(__name__)
server = app.server
content=pd.read_csv('assets/StartSet.csv',header=None).dropna(how='all',axis=1).dropna(how='all',axis=0)
content=content.fillna('')
titoli=['% Anno','ISIN Certificato','Prima Cedola','Ultima Cedola','Emittente','Nome Sottostante','Codice yahoo_fin Sottostante','Strike','Barriera','Mercato','Vicinanza alla barriera']
fixed=['% Anno','ISIN Certificato','Prima Cedola','Ultima Cedola','Emittente','Nome Sottostante','Codice yahoo_fin Sottostante','Strike','Barriera']
colonne=[{'id':name, 'name':name, 'editable':True} for name in fixed]+\
    [{'id':'Mercato','name':'Mercato','type':'numeric','format':euroformat,'editable':False}]+\
    [{'id':'Vicinanza alla barriera','name':'Vicinanza alla barriera','type':'numeric','format':FormatTemplate.percentage(1),'editable':False}]
content.columns=titoli 
try:
    with open('file','r') as file:
        start_message=file.readlines()[0]
except:
    start_message='Mai aggiornato, clicca per aggiornare'
start_data=content.to_dict(orient='records')
app.layout=html.Div(children=[
                            dcc.Interval(
                                id='interval_component',
                                interval=10*60*1000,
                                n_intervals=0),
                            dcc.Store(id='local', storage_type='local'),
                            html.H1('Certificati Gianni',style={'text-align':'center'}),
                            html.Div(children=[
                            html.Div(children=[html.Button(id='update_button',children='Aggiorna prezzi di mercato'),
                                               html.H5(id='update_message',children=start_message)
                            ]),
                            html.Button(id='add_row',children='Aggiungi un rigo alla tabella')],style={'display':'table-row'}),
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
                                                ,
                                                {
                                                    'if': {'filter_query':'{Vicinanza alla barriera}<0',
                                                           'column_id': 'Vicinanza alla barriera'},
                                                    'color': 'white',
                                                    'backgroundColor':'white',
                                                },
                                                {
                                                    'if': {'filter_query':'{Vicinanza alla barriera}>0.6',
                                                           'column_id': 'Vicinanza alla barriera'},
                                                    'color': 'white',
                                                    'backgroundColor':'orange',
                                                },
                                                {
                                                    'if': {'filter_query':'{Vicinanza alla barriera}>0.8',
                                                           'column_id': 'Vicinanza alla barriera'},
                                                    'color': 'white',
                                                    'backgroundColor':'red',
                                                },
                                                {
                                                    'if': {'filter_query':'{{Vicinanza alla barriera}}={}'.format('SUPERATA!'),
                                                           'column_id': 'Vicinanza alla barriera'},
                                                    'color': 'white',
                                                    'backgroundColor':'red',
                                                }
                                                #,
                                                # {
                                                #     'if': {
                                                #         'filter_query': '{{Mercato}}0',
                                                #         'column_id': 'Mercato'
                                                #     },
                                                #     'color': 'white'
                                                # }
                                            ],
                                          columns=colonne,
                                          #page_size=30,
                                          filter_action="native",
                                          editable=True,
                                          sort_action="native",
                                          sort_mode="multi",
                                          row_deletable=True
                                        ),
                type="circle",
                fullscreen=True)])

@callback(
    Output('Tabella principale', 'data',allow_duplicate=True),
    Input('add_row', 'n_clicks'),
    State('Tabella principale', 'data'),
    State('Tabella principale', 'columns'),
    prevent_initial_call=True
)
def add_row(n_clicks, rows, columns):
    if n_clicks:
        rows.append({c['id']: '' for c in columns})
    return rows

@callback(
    Output(component_id=f'Tabella principale', component_property='data'),
    Output(component_id=f'update_message',component_property='children'),
    Input(component_id=f'update_button', component_property='n_clicks'),
    Input(component_id=f'interval_component', component_property='n_intervals'),
    State(component_id=f'Tabella principale', component_property='data'),
)
def update_post_tables(click_to_update,n,old_data):
    #if not click_to_update:
    #    raise PreventUpdate
    logging.error(f'CLICKED:{click_to_update}, INTERVALS PASSED: {n}')
    data=old_data
    #print(f'old_data={old_data}')
    tickers=[line['Codice yahoo_fin Sottostante'].replace('\r','').upper() for line in old_data]
    #print(f'tickers={tickers}')
    quotes={}
    for ticker in tickers:
        ticker=ticker.upper()
    for ticker in list(set(tickers)):
        quotes[ticker]=get_live_price(ticker)
    for line in old_data:
        valore=float(quotes[line['Codice yahoo_fin Sottostante'].replace('\r','').upper()])
        barriera=float(line['Barriera'].replace(',','.'))
        strike=float(line['Strike'].replace(',','.'))
        vicinanza=int((strike-valore)/(strike-barriera)*1000)/1000
        if vicinanza>1:
            vicinanza='SUPERATA!'
        logging.info(f'valore:{valore},barriera:{barriera},strike:{strike}')
        print(f'valore:{valore},barriera:{barriera},strike:{strike}')
        line.update({'Mercato':valore,
                    'Vicinanza alla barriera':vicinanza})
    data=[line for line in old_data]
    #print(f'new_data:{data}')
    df=pd.DataFrame.from_records(data)         
    df.to_csv('assets/StartSet.csv',index=False,header=False)

    update_message=f"Aggiornato l'ultima volta alle {datetime.datetime.now()}"
    with open('file','w') as file:
        file.write(update_message)
    return data,update_message


#def load_data():


if __name__ == '__main__':
    app.run(port="1234", debug=False)
    #sched = BackgroundScheduler()
    #sched.add_job(func=load_data, trigger='interval', seconds=10)
    #sched.start()