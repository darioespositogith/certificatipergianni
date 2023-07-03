from dash import Dash, html, dcc, Input,Output,State, callback
from dash.exceptions import PreventUpdate
from dash.dash_table import *
from dash.dash_table.Format import Format, Scheme, Group, Symbol
from yahoo_fin.stock_info import *
import os
import logging
import requests
import json
from teleborsaconfig import *
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
content=pd.read_csv('assets/StartSet.csv',header=None,sep="£").dropna(how='all',axis=1).dropna(how='all',axis=0)
content=content.fillna('')
titoli=['% Anno','ISIN Cert.','1° Ced.','Ultima Ced.','Emittente','Sottostante','Codice Sottostante','Strike','Barriera','Prezzo Sottostante','Vicinanza Barriera','Bid Cert.','Ask Cert.']
fixed=['% Anno','ISIN Cert.','1° Ced.','Ultima Ced.','Emittente','Sottostante','Codice Sottostante']
colonne=[{'id':name, 'name':name, 'editable':True} for name in fixed]+\
    [{'id':'Strike','name':'Strike','type':'numeric','format':euroformat,'editable':True}]+\
    [{'id':'Barriera','name':'Barriera','type':'numeric','format':euroformat,'editable':True}]+\
    [{'id':'Prezzo Sottostante','name':'Prezzo Sottostante','type':'numeric','format':euroformat,'editable':False}]+\
    [{'id':'Vicinanza Barriera','name':'Vicinanza barriera','type':'numeric','format':FormatTemplate.percentage(1),'editable':False}]+\
    [{'id':'Bid Cert.','name':'Bid Cert.','type':'numeric','format':euroformat,'editable':False}]+\
    [{'id':'Ask Cert.','name':'Ask Cert.','type':'numeric','format':euroformat,'editable':False}]
content.columns=titoli 
try:
    with open('file','r') as file:
        start_message=file.readlines()[0]
except:
    start_message='Mai aggiornato, clicca per aggiornare'
start_data=content.to_dict(orient='records')
app.layout=html.Div(children=[
    dcc.Store(id='nothing',data={}),
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
                            html.Div(id='niente',children=[html.H5('Aggiungi un url teleborsa per eventuali siti che non rispondono. Per ISIN ',style={'display':'inline-block'}),dcc.Input(id='isin',type='text',placeholder='ISIN',style={'display':'inline-block'}),html.H5("cerca all'indirizzo: ",style={'display':'inline-block'}),dcc.Input(id='url_completo',type='text',placeholder='www.etc....',style={'display':'inline-block'}),
                            html.Button(id='add_tb_link',children='Aggiungi!',style={'display':'inline-block'})],
                                     style={'display':'inline-block'}),
                            dcc.Loading(DataTable(id='Tabella principale',
                                          data=start_data,
                                          #{name:'' for name in ['% Anno','ISIN Certificato','Prima Cedola','Ultima Cedola','Emittente','Nome Sottostante','Codice yahoo_fin Sottostante','Strike','Barriera','Mercato']}],
                                          style_data={
                                            'whiteSpace': 'nowrap',
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
                                                    'if': {'filter_query':'{Vicinanza Barriera}<0',
                                                           'column_id': 'Vicinanza Barriera'},
                                                    'color': 'white',
                                                    'backgroundColor':'white',
                                                },
                                                {
                                                    'if': {'filter_query':'{Vicinanza Barriera}>0.6',
                                                           'column_id': 'Vicinanza Barriera'},
                                                    'color': 'white',
                                                    'backgroundColor':'orange',
                                                },
                                                {
                                                    'if': {'filter_query':'{Vicinanza Barriera}>0.8',
                                                           'column_id': 'Vicinanza Barriera'},
                                                    'color': 'white',
                                                    'backgroundColor':'red',
                                                },
                                                {
                                                    'if': {'filter_query':'{{Vicinanza Barriera}}={}'.format('SUPERATA!'),
                                                           'column_id': 'Vicinanza Barriera'},
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
    Output('nothing','data'),
    Input('add_tb_link', 'n_clicks'),
    State('isin','value'),
    State('url_completo','value'),
    prevent_initial_call=True
)
def add_teleborsalink(n_clicks, isin,url):
    if not n_clicks:
        raise PreventUpdate
    with open('teleborsaconfig.py','r') as file:
        mapping=json.load(file)
    mapping[isin]=url
    with open('teleborsaconfig.py','w') as file:
        json.dump(mapping,file,indent=6)
    return {}

@callback(
    Output(component_id=f'Tabella principale', component_property='data'),
    Output(component_id=f'update_message',component_property='children'),
    Input(component_id=f'update_button', component_property='n_clicks'),
    Input(component_id=f'interval_component', component_property='n_intervals'),
    State(component_id=f'Tabella principale', component_property='data'),
)
def update_post_tables(click_to_update,n,old_data):
    with open('teleborsaconfig.py','r') as file:
        mapping=json.load(file)
    logging.error(f'CLICKED:{click_to_update}, INTERVALS PASSED: {n}')
    data=old_data
    #logging.error(f'old_data={old_data}')
    tickers=[line['Codice Sottostante'].replace('\r','').upper() for line in old_data]
    dizionario_isin_emittente={line['ISIN Cert.'].replace('\r','').upper():line['Emittente'].replace('\r','').upper() for line in old_data}
    logging.error(dizionario_isin_emittente)
    for isin in dizionario_isin_emittente.keys():
        logging.error(f'Sto provando a scaricare {isin} da {dizionario_isin_emittente[isin]}')
        if isin=='':
            dizionario_isin_emittente[isin]=('','')
        elif dizionario_isin_emittente[isin]=='LQ':
            r=requests.get(url=f'https://certificati.leonteq.com/api/product-model/details/isin/{isin}?language_id=1')
            bid=r.json()['product']['bid']['initialValue']
            if 'initialValue' in r.json()['product']['ask'].keys():
                ask=r.json()['product']['ask']['initialValue']
            else: 
                logging.error(f"ATTENZIONE CHE QUA con isin={isin} i valori SONO {r.json()['product']['ask']}")
                ask='Sito non risponde'
            dizionario_isin_emittente[isin]=(bid,ask)
            logging.error(dizionario_isin_emittente[isin])
        elif dizionario_isin_emittente[isin]=='UNI':
            r=requests.get(url=f"https://www.investimenti.unicredit.it/{isin.replace('DE0000','')[:-1]}")
            risultato_testuale=r.text
            if '<span class="bid">' in risultato_testuale:
                bid=risultato_testuale.split('<span class="bid">')[1].split('</span>')[0]
                ask=risultato_testuale.split('<span class="ask">')[1].split('</span>')[0]
                dizionario_isin_emittente[isin]=(bid,ask)
                logging.error(dizionario_isin_emittente[isin])
            else:
                (bid,ask)=('Sito non risponde','Sito non risponde')
                dizionario_isin_emittente[isin]=('Sito non risponde','Sito non risponde')
                logging.error(dizionario_isin_emittente[isin])
        elif dizionario_isin_emittente[isin]=='BNP':
            r=requests.get(url=f"https://investimenti.bnpparibas.it/product-details/{isin}/")
            risultato_testuale=r.text
            if 'data-field="bid"' in risultato_testuale:
                bid=risultato_testuale.split('data-field="bid"')[1].split('</span>')[0].split('>')[-1]
                if 'data-field="ask"' in risultato_testuale:
                    ask=risultato_testuale.split('data-field="ask"')[1].split('</span>')[0].split('>')[-1]
                else:
                    ask='bid-only!'
            else:
                (bid,ask)=('Sito non risponde','Sito non risponde')
            dizionario_isin_emittente[isin]=(bid,ask)
            logging.error(dizionario_isin_emittente[isin])
        elif dizionario_isin_emittente[isin]=='VON':
            r=requests.get(url=f"https://certificati.vontobel.com/IT/IT/Prodotti/{isin}/")
            risultato_testuale=r.text
            with open(f"{isin}.txt",'w') as file:
                file.write(risultato_testuale)
            if '<span class="title">Denaro</span><span class="strong value">' in risultato_testuale:
                bid=risultato_testuale.split('<span class="title">Denaro</span><span class="strong value">')[1].split('</span>')[0]
                if '<span class="title">Lettera</span><span class="strong value">' in risultato_testuale:
                    ask=risultato_testuale.split('<span class="title">Lettera</span><span class="strong value">')[1].split('</span>')[0]
                else:
                    ask='bid-only!'
            else:
                (bid,ask)=('Sito non risponde','Sito non risponde')
            dizionario_isin_emittente[isin]=(bid,ask)
            logging.error(dizionario_isin_emittente[isin])
        elif dizionario_isin_emittente[isin]=='MAF':
            (bid,ask)=('Sito non risponde','Sito non risponde')
            dizionario_isin_emittente[isin]=(bid,ask)
            logging.error(dizionario_isin_emittente[isin])
        else:
            dizionario_isin_emittente[isin]=('','')
        
        ##########
        # TENTATIVI INDIVIDUALI CON TELEBORSA
        ##########
        if bid=='Sito non risponde' or dizionario_isin_emittente[isin][0]=='Sito non risponde' or dizionario_isin_emittente[isin][0]=='':
            print(f'Qui isin è {isin} e mi chiedo se si trovi in {mapping.keys()}')
            if isin in mapping.keys():
                print('E ci sta!')
                r=requests.get(url=mapping[isin])
                risultato_testuale=r.text
                if '"ctl00_phContents_ctlInfoTitolo_lblBid"' in risultato_testuale:
                    print('Ho trovato quello che volevo!!!\n\n\n')
                    bid=risultato_testuale.split('"ctl00_phContents_ctlInfoTitolo_lblBid">')[1].split('</span>')[0].split(' x')[0]
                    if '"ctl00_phContents_ctlInfoTitolo_lblAsk"' in risultato_testuale:
                        ask=risultato_testuale.split('"ctl00_phContents_ctlInfoTitolo_lblAsk">')[1].split('</span>')[0].split(' x')[0]
                    else:
                        ask='bid-only!'
                else:
                    (bid,ask)=('Sito non risponde','Sito non risponde')
                
                dizionario_isin_emittente[isin]=(bid,ask)
                logging.error(dizionario_isin_emittente[isin])








    quotes={}
    for ticker in tickers:
        ticker=ticker.upper()
    for ticker in list(set(tickers)):
        quotes[ticker]=get_live_price(ticker)
    for line in old_data:
        valore=float(quotes[line['Codice Sottostante'].replace('\r','').upper()])
        if type(line['Barriera'])==str:
            barriera=float(line['Barriera'].replace(',','.'))
            strike=float(line['Strike'].replace(',','.'))
        else:
            barriera=float(line['Barriera'])
            strike=float(line['Strike'])
        vicinanza=int((strike-valore)/(strike-barriera)*1000)/1000
        if vicinanza>1:
            vicinanza='SUPERATA!'
        #logging.error(f'valore:{valore},barriera:{barriera},strike:{strike}')
        #logging.error(f'valore:{valore},barriera:{barriera},strike:{strike}')
        line.update({'Barriera':barriera,
                     'Strike':strike,
                    'Prezzo Sottostante':valore,
                    'Vicinanza Barriera':vicinanza,
                    'Bid Cert.':str(dizionario_isin_emittente[line['ISIN Cert.']][0]).replace('\t','').replace(' ','').replace('\n','').replace('\r',''),
                    'Ask Cert.':str(dizionario_isin_emittente[line['ISIN Cert.']][1]).replace('\t','').replace(' ','').replace('\n','').replace('\r','')}
                    )
    data=[line for line in old_data]
    #logging.error(f'new_data:{data}')
    df=pd.DataFrame.from_records(data)         
    df.to_csv('assets/StartSet.csv',index=False,header=False,sep="£")

    update_message=f"Aggiornato l'ultima volta alle {datetime.datetime.now()+datetime.timedelta(hours=2)}"
    with open('file','w') as file:
        file.write(update_message)
    return data,update_message


#def load_data():


if __name__ == '__main__':
    app.run(port="1234", debug=False)
    #sched = BackgroundScheduler()
    #sched.add_job(func=load_data, trigger='interval', seconds=10)
    #sched.start()