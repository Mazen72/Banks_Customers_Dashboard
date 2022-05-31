import time
import os
import dash
import pandas as pd
import base64
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask
import io
from dash import Dash, Input, Output, dash_table, callback_context, State
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.exceptions import PreventUpdate
import Functions
from collections import OrderedDict
from dash.dcc import Download, send_data_frame
from fpdf import FPDF

# defining server object
server = Flask(__name__)

# defining app object
app = dash.Dash(
    __name__,server=server,
    meta_tags=[
        {
            'charset': 'utf-8',
        },
        {
            'name': 'viewport',
            'content': 'width=device-width, initial-scale=1.0, shrink-to-fit=no'
        }
    ] ,
)

# setting the title of the app which will be shown in browser tab
app.title='Customers Dashboard'

# setting some error handling in the app
app.config.suppress_callback_exceptions = True

# getting the local directory of the app
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

# reading the database ( excel file ) from the app local directory
excel_file = os.path.join(THIS_FOLDER, 'databse.xlsx')

# reading the icon image from the app local directory
icon_img= os.path.join(THIS_FOLDER, 'banks_icon.jpg')

# a dictionery contains some colors used in some parts of the app layout
base_colors={ 'color1': '#EBECF0', 'color2': '#F5F5F5','color3': '#0f70e0'}

# setting a font size that is used in some parts of the app layout
text_font_size='1.5vh'

'''
-------- Frontend Part --------
'''

# creating the header text component on the top of the app
header_text=html.Div('Banks Customers Dashboard',id='main_header_text',className='main-header',
                     style=dict(color=base_colors['color3'],
                     fontWeight='bold',fontSize='2.4vh',marginTop='',marginLeft='',width='100%',paddingTop='1%',paddingBottom='',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))

# setting the spacing of the of the header text component
db_header_text=  dbc.Col([ header_text] ,
        xs=dict(size=10,offset=0), sm=dict(size=10,offset=0),
        md=dict(size=8,offset=0), lg=dict(size=6,offset=0), xl=dict(size=6,offset=0))

# processing the icon image and creating image component
encoded = base64.b64encode(open(icon_img, 'rb').read())
logo_img=html.Img(src='data:image/jpg;base64,{}'.format(encoded.decode()), id='logo_img', height='60px',width='60px',
                  style=dict(paddingLeft='',border=''.format(['Main Header Background'][0])))

# setting the spacing of the of the image component
db_logo_img=dbc.Col([ logo_img] ,
        xs=dict(size=2,offset=0), sm=dict(size=2,offset=0),
        md=dict(size=2,offset=0), lg=dict(size=3,offset=0), xl=dict(size=3,offset=0))

# reading the database into a dataframe
dff=pd.read_excel(excel_file,sheet_name='data',engine='openpyxl')

# taking only the columns we are interested in to reduce processing time
df=dff[['ide','bank_name','customer_id','customer_name','transaction_value','deposited_value','to_be_paid','approval_date','sector_name4','rate_JUCAS','rate_bank','time_amortization']]

# converting the type of customer_id column to string to be easier to work with
df['customer_id']=df['customer_id'].astype(str)

# converting the type of approval_date column to datetime to be able to use pandas datetime special functions
df['approval_date']= pd.to_datetime(df['approval_date'],format="%d/%m/%Y")

# creating a new column which contain only years from approval_date column
df['Year'] = (pd.DatetimeIndex(df['approval_date']).year).astype(str)

# creating a list of all unique customers ids from the customer_id column
customers_ids_list=df['customer_id'].unique()

# choosing the initial customer_id that we will show its data in the app startup
df_customer=df[df['customer_id']==df['customer_id'][14] ]

# creating a list of all unique banks names in the filtered customer dataframe from the bank_name column
customer_banks_list=list( df_customer['bank_name'].unique() )

# creating a list of all unique sectors names in the filtered customer dataframe from the sector_name4 column
customer_sectors_list=list( df_customer['sector_name4'].unique() )

# adding 'All Banks' and 'All Sectors' options in the created lists
customer_banks_list.insert(0,'All Banks')
customer_sectors_list.insert(0,'All Sectors')

# creating a list of all unique years in the filtered customer dataframe
df_customer['Year'] = (pd.DatetimeIndex(df_customer['approval_date']).year).astype(str)
years=df_customer['Year'].to_list()
years=list(OrderedDict.fromkeys(years))
years.insert(0,'All Years')

# adjusing the indicators ( info in blue cards ) sizes and colors
indicator_size=22
indicator_text_color='white'
indicator_bg_color=base_colors['color3']
indicator_height=40

# creating Transactions Sum card header
sum_trans_text= html.Div(html.H1('Transactions Sum',className= 'info-header',
                                    style=dict(fontSize='', fontWeight='bold', color=indicator_text_color,
                                               marginTop='')),
                            style=dict(display='', marginLeft='', textAlign="center", width='100%'))

# initializing an empty figure where it will contain the Transactions Sum info ( number )
sum_trans_fig=go.Figure()
sum_trans_indicator=html.Div(dcc.Graph(figure=sum_trans_fig,config={'displayModeBar': False},id='sum_trans_indicator',style=dict(width='100%')),className='num'
                           , style=dict(width='100%')  )

# creating Deposit Sum card header
sum_dep_text= html.Div(html.H1('Deposits Sum',className= 'info-header',
                                    style=dict(fontSize='', fontWeight='bold', color=indicator_text_color,
                                               marginTop='')),
                            style=dict(display='', marginLeft='', textAlign="center", width='100%'))

# initializing an empty figure where it will contain the Deposit Sum info ( number )
sum_dep_fig=go.Figure()
sum_dep_indicator=html.Div(dcc.Graph(figure=sum_dep_fig,config={'displayModeBar': False},id='sum_dep_indicator',style=dict(width='100%')),className='num'
                           , style=dict(width='100%')  )

# creating Avg Jucas Rating card header
avg_ratej_text= html.Div(html.H1('Avg Jucas Rating',className= 'info-header',
                                    style=dict(fontSize='', fontWeight='bold', color=indicator_text_color,
                                               marginTop='')),
                            style=dict(display='', marginLeft='', textAlign="center", width='100%'))

# initializing an empty figure where it will contain the Avg Jucas Rating info ( number )
avg_ratej_fig=go.Figure()
avg_ratej_indicator=html.Div(dcc.Graph(figure=avg_ratej_fig,config={'displayModeBar': False},id='avg_ratej_indicator',style=dict(width='100%')),className='num'
                           , style=dict(width='100%')  )


# same with the remaining cards

avg_rateb_text= html.Div(html.H1('Avg Bank Rating',className= 'info-header',
                                    style=dict(fontSize='', fontWeight='bold', color=indicator_text_color,
                                               marginTop='')),
                            style=dict(display='', marginLeft='', textAlign="center", width='100%'))

avg_rateb_fig=go.Figure()

avg_rateb_indicator=html.Div(dcc.Graph(figure=avg_rateb_fig,config={'displayModeBar': False},id='avg_rateb_indicator',style=dict(width='100%')),className='num'
                           , style=dict(width='100%')  )


avg_time_text= html.Div(html.H1('Avg Amortization Time',className= 'info-header',
                                    style=dict(fontSize='', fontWeight='bold', color=indicator_text_color,
                                               marginTop='')),
                            style=dict(display='', marginLeft='', textAlign="center", width='100%'))

avg_time_fig=go.Figure()

avg_time_indicator=html.Div(dcc.Graph(figure=avg_time_fig,config={'displayModeBar': False},id='avg_time_indicator',style=dict(width='100%')),className='num'
                           , style=dict(width='100%')  )


to_be_paid_text= html.Div(html.H1('To be Paid Sum',className= 'info-header',
                                    style=dict(fontSize='', fontWeight='bold', color=indicator_text_color,
                                               marginTop='')),
                            style=dict(display='', marginLeft='', textAlign="center", width='100%'))

to_be_paid_fig=go.Figure()

to_be_paid_indicator=html.Div(dcc.Graph(figure=to_be_paid_fig,config={'displayModeBar': False},id='to_be_paid_indicator',style=dict(width='100%')),className='num'
                           , style=dict(width='100%')  )

op_count_text= html.Div(html.H1('Operations Count',className= 'info-header',
                                    style=dict(fontSize='', fontWeight='bold', color=indicator_text_color,
                                               marginTop='')),
                            style=dict(display='', marginLeft='', textAlign="center", width='100%'))

op_count_fig=go.Figure()

op_count_indicator=html.Div(dcc.Graph(figure=op_count_fig,config={'displayModeBar': False},id='op_count_indicator',style=dict(width='100%')),className='num'
                           , style=dict(width='100%')  )

# setting the dropdown menus sizes and colors
dropdowns_font='black'
dropdowns_bg='#DCDCDC'
dropdowns_bg_radius='5%'
dropdowns_border='#BEBEBE'
dropdowns_width='16%'

# creating customer_id dropdown menu
customer_id_menu = dcc.Dropdown(
    options=[{'label': id , 'value': id} for id in customers_ids_list],
    value=df['customer_id'][14],
    id='customer_id_menu',
    style=dict(color=dropdowns_font, fontWeight='bold', textAlign='center',borderRadius=dropdowns_bg_radius,
               width='100%', backgroundColor=dropdowns_bg, border='1px solid {}'.format(dropdowns_border) )
)

customer_id_text = html.Div(html.H1('Customer ID',
                              style=dict(fontSize=text_font_size, fontWeight='bold', color='black',
                                         marginTop='')),
                      style=dict(display='inline-block', marginLeft='', textAlign="center", width='100%'))

customer_id_div = html.Div([customer_id_text, customer_id_menu],
                     style=dict(fontSize=text_font_size,
                                marginLeft='', marginBottom='', display='inline-block',width=dropdowns_width))

# creating bank_name dropdown menu
banks_names_menu = dcc.Dropdown(
    options=[{'label': name, 'value': name} for name in customer_banks_list],
    value=customer_banks_list[0],
    id='banks_names_menu',
    style=dict(color=dropdowns_font, fontWeight='bold', textAlign='center',borderRadius=dropdowns_bg_radius,
               width='100%', backgroundColor=dropdowns_bg, border='1px solid {}'.format(dropdowns_border) )
)

banks_names_text = html.Div(html.H1('Bank Name',
                              style=dict(fontSize=text_font_size, fontWeight='bold', color='black',
                                         marginTop='')),
                      style=dict(display='inline-block', marginLeft='', textAlign="center", width='100%'))

banks_names_div = html.Div([banks_names_text, banks_names_menu],
                     style=dict(fontSize=text_font_size,
                                marginLeft='2vw', marginBottom='', display='inline-block',width=dropdowns_width))

# creating sector_name4 dropdown menu
sectors_names_menu = dcc.Dropdown(
    options=[{'label': name, 'value': name} for name in customer_sectors_list],
    value=customer_sectors_list[0],
    id='sectors_names_menu',
    style=dict(color=dropdowns_font, fontWeight='bold', textAlign='center',borderRadius=dropdowns_bg_radius,
               width='100%', backgroundColor=dropdowns_bg, border='1px solid {}'.format(dropdowns_border) )
)

sectors_names_text = html.Div(html.H1('Sector Name',
                              style=dict(fontSize=text_font_size, fontWeight='bold', color='black',
                                         marginTop='')),
                      style=dict(display='inline-block', marginLeft='', textAlign="center", width='100%'))

sectors_names_div = html.Div([sectors_names_text, sectors_names_menu],
                     style=dict(fontSize=text_font_size,
                                marginLeft='2vw', marginBottom='', display='inline-block',width=dropdowns_width))

# creating years dropdown menu
years_menu = dcc.Dropdown(
    options=[{'label': year, 'value': year} for year in years],
    value=years[0],
    id='years_menu',
    style=dict(color=dropdowns_font, fontWeight='bold', textAlign='center',borderRadius=dropdowns_bg_radius,
               width='100%', backgroundColor=dropdowns_bg, border='1px solid {}'.format(dropdowns_border) )
)

years_text = html.Div(html.H1('Year',
                              style=dict(fontSize=text_font_size, fontWeight='bold', color='black',
                                         marginTop='')),
                      style=dict(display='inline-block', marginLeft='', textAlign="center", width='100%'))

years_div = html.Div([years_text, years_menu],
                     style=dict(fontSize=text_font_size,
                                marginLeft='2vw', marginBottom='', display='inline-block',width=dropdowns_width))

# creating the button that will apply the dropdowns filters to all graphs when clicked
apply_button = html.Div(dbc.Button(
    "Apply Filters", id="apply_button", n_clicks=0, size='lg',
    style=dict(fontSize=text_font_size, backgroundColor='#119DFF',color='white',fontWeight='bold')
), style=dict(textAlign='center', display='inline-block', marginTop='1.5%', paddingLeft='2vw',width='20%'))

# creating the layout ( row , column ) that will contain the previous dropdowns and button
menues_row = html.Div([customer_id_div,sectors_names_div,banks_names_div,years_div,apply_button],
                       style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                                      'justify-content': 'center'})

menues_column=dbc.Col(  html.Div(dbc.Card(dbc.CardBody([menues_row
                                                          ])
                                            , style=dict(backgroundColor='white', width='100%',
                                            border=''), id='card2',
                                            className='menus-card'),style=dict(display= 'flex', alignItems= 'center',
                                                        justifyContent= 'center',width='100%'))
,        xs=dict(size=12,offset=0), sm=dict(size=12,offset=0),
        md=dict(size=8,offset=2), lg=dict(size=6,offset=0), xl=dict(size=6,offset=0))

# creating the customer name section
customer_name_text = html.Div(html.Div('CUSTOMER13',id='customer_name_text',
                              style=dict(fontSize='1.6vh', fontWeight='bold', color='black',
                                         marginTop='')),
                      style=dict(display='', marginLeft='', textAlign="center", width='100%'))


customer_name_header = html.Div(html.H1('Customer Name',
                              style=dict(fontSize='2vh', fontWeight='bold', color='black',
                                         marginTop='')),
                      style=dict(display='', marginLeft='', textAlign="center", width='100%'))

customer_name_div = html.Div([customer_name_header, dbc.Spinner([customer_name_text], size="lg", color="primary",
                                                                  type="border", fullscreen=False,
                                                                  spinner_style=dict(marginTop=''))],
                     style=dict(fontSize=text_font_size,
                                marginLeft='', display='',width='100%'))

customer_name_col=dbc.Col(  html.Div(dbc.Card(dbc.CardBody([customer_name_div
                                                          ])
                                            , style=dict(backgroundColor='white', width='100%',
                                            border=''), id='name_card',
                                            className='menus-card')  ,style=dict(display= 'flex', alignItems= 'center',
                                                        justifyContent= 'center',width='100%'))
,        xs=dict(size=12,offset=0), sm=dict(size=12,offset=0),
        md=dict(size=8,offset=2), lg=dict(size=3,offset=0), xl=dict(size=3,offset=0) ,
                            style=dict( paddingRight='2vw'))

# creating the download excel section
download_excel=html.Div([Download(id="download_excel")])

download_excel_button = html.Div(dbc.Button(
    "Download Excel", id="download_excel_button", n_clicks=0, size='lg',
    style=dict(fontSize='1.4vh', backgroundColor='#119DFF',color='white',fontWeight='bold')
), style=dict(textAlign='center', display='', marginTop='1.5%', paddingLeft='',width=''))

download_excel_text = html.Div(html.H1('Download Customer Data',
                              style=dict(fontSize='1.6vh', fontWeight='bold', color='black',
                                         marginTop='')),
                      style=dict(textAlign="center", width='100%'))

excel_output=html.Div(id='excel_output')

download_excel_div = html.Div([download_excel_text,download_excel_button,download_excel,excel_output],
                       style={'width': '100%'})
download_excel_row=html.Div(download_excel_div,style=dict(display= 'flex', alignItems= 'center',
                                                        justifyContent= 'center',width='100%'))

download_excel_col=dbc.Col( dbc.Card(dbc.CardBody([download_excel_row
                                                          ])
                                            , style=dict(backgroundColor='white', width='',
                                            border=''), id='excel_card',
                                            className='excel-card')
,        xs=dict(size=12,offset=0), sm=dict(size=12,offset=0),
        md=dict(size=8,offset=2), lg=dict(size=2,offset=1), xl=dict(size=2,offset=1) ,
                            style=dict( paddingRight=''))


# creating the section of the histogram graph
hist_fig=go.Figure(go.Histogram())
hist_div=html.Div(id='operations_hist_div')

hist_div_col=dbc.Col( dbc.Card(dbc.CardBody([ html.Div([dbc.Spinner([hist_div],size="lg", color="primary", type="border", fullscreen=False )


                                        ], style=dict(height=''))
                                                          ])
                                            , style=dict(backgroundColor='white', width='100%',
                                            border=''), id='hist_card',
                                            className='charts-card')
,        xs=dict(size=12,offset=0), sm=dict(size=12,offset=0),
        md=dict(size=6,offset=0), lg=dict(size=5,offset=0), xl=dict(size=5,offset=0) ,
                            style=dict(paddingRight=''))


# creating the section of the line chart
resolution_menu = dcc.Dropdown(
    options=[
        dict(label='Sum Yearly', value='Sum Yearly'), dict(label='Sum Quarterly', value='Sum Quarterly'),
        dict(label='Sum Monthly', value='Sum Monthly'), dict(label='Sum Daily', value='Sum Daily'),

    ],
    value='Sum Monthly' ,
    id='resolution_menu',
    style=dict(color=dropdowns_font, fontWeight='bold', textAlign='center',borderRadius=dropdowns_bg_radius,
               width='100%', backgroundColor=dropdowns_bg, border='1px solid {}'.format(dropdowns_border) )
)

resolution_text = html.Div(html.H1('Date Resolution',
                              style=dict(fontSize=text_font_size, fontWeight='bold', color='black',
                                         marginTop='')),
                      style=dict(display='inline-block', marginLeft='', textAlign="center", width='100%'))

resolution_menu_div = html.Div([resolution_menu],
                     style=dict(fontSize='1.4vh',
                                marginLeft='', marginBottom='', display='inline-block',width='22%'))

resolution_menu_row=html.Div([resolution_menu_div],style=dict(display='flex', alignItems='center',
                                      justifyContent='center', width='100%'))

line_chart_div = html.Div(id='line_chart_div')

line_chart_col= dbc.Col([dbc.Card(dbc.CardBody([
                                                dbc.Spinner([line_chart_div], size="lg", color="primary", type="border",
                                                                    fullscreen=False) , html.Br(),resolution_menu_row

                                                        ])
                                          , style=dict(backgroundColor='white'), id='card17',
                                          className='charts-card'), html.Br()
                                 ], xl=dict(size=5, offset=1), lg=dict(size=5, offset=1),
                                md=dict(size=6, offset=0), sm=dict(size=12, offset=0), xs=dict(size=12, offset=0),
                                style=dict(paddingLeft='0.5vw',paddingRight='0.5vw'))

# creating the section of the stacked bar chart
stacked_bar_chart_div=html.Div(id='stacked_bar_chart_div')
stacked_bar_chart_col=dbc.Col( dbc.Card(dbc.CardBody([ html.Div([dbc.Spinner([stacked_bar_chart_div]
                                                    ,size="lg", color="primary", type="border", fullscreen=False )


                                        ], style=dict(height=''))
                                                          ])
                                            , style=dict(backgroundColor='white', width='100%',
                                            border=''), id='stacked_card',
                                            className='charts-card')
,        xs=dict(size=12,offset=0), sm=dict(size=12,offset=0),
        md=dict(size=6,offset=0), lg=dict(size=5,offset=1), xl=dict(size=5,offset=1) ,
                            style=dict(paddingLeft='0.5vw',paddingRight='0.5vw'))

# creating the section of the tabke with the download pdf button
download_pdf_button = html.Div(dbc.Button(
    "Generate PDF Report", id="download_pdf_button", n_clicks=0, size='lg',
    style=dict(fontSize='1.4vh', backgroundColor='#119DFF',color='white',fontWeight='bold')
), style=dict(textAlign='center', display='', marginTop='1.5vh', paddingLeft='',width=''))

pdf_output=dbc.Spinner([dbc.Alert("Downloaded Succesfully",id="pdf_output",is_open=False,duration=4000,style=dict(marginTop='2vh'))]
                       , size="sm", color="primary",type="border", fullscreen=False,spinner_style=dict(marginTop=''))

pdf_div=html.Div([download_pdf_button,pdf_output])
pdf_row=html.Div(pdf_div,style=dict(display= 'flex', alignItems= 'center',
                                                        justifyContent= 'center',width='100%'))

customer_table_div=html.Div(id='customer_table_div')
customer_table_col=dbc.Col( dbc.Card(dbc.CardBody([ html.Div([dbc.Spinner([customer_table_div]
                                                    ,size="lg", color="primary", type="border", fullscreen=False )


                                        ], style=dict(height='')),pdf_row
                                                          ])
                                            , style=dict(backgroundColor='white', width='100%',
                                            border=''), id='table_card',
                                            className='table-card')
,        xs=dict(size=12,offset=0), sm=dict(size=12,offset=0),
        md=dict(size=6,offset=0), lg=dict(size=5,offset=0), xl=dict(size=5,offset=0) ,
                            style=dict(paddingLeft='0.5vw',paddingRight='0.5vw'))


# putting all the previous components in the app layout object
app.layout=html.Div([

dbc.Row([db_logo_img,db_header_text],
                              style=dict(backgroundColor=base_colors['color1']),id='main_header' )
,dbc.Row([download_excel_col,menues_column,customer_name_col]) , html.Br(),

dbc.Row([
                        html.Div([

                      dbc.Card( [ dbc.CardHeader(sum_trans_text),
                          dbc.CardBody([
                                                      dbc.Spinner([sum_trans_indicator], size="lg", color="light",
                                                                  type="border", fullscreen=False,
                                                                  spinner_style=dict(marginTop=''))

                                                      ])]
                                        , style=dict(backgroundColor=indicator_bg_color), id='card3',
                                        className='info-card'),


                      dbc.Card([dbc.CardHeader(sum_dep_text),
                          dbc.CardBody([
                                                      dbc.Spinner([sum_dep_indicator], size="lg", color="light",
                                                                  type="border", fullscreen=False,
                                                                  spinner_style=dict(marginTop=''))

                                                      ])]
                                        , style=dict(backgroundColor=indicator_bg_color,marginLeft='1vw'), id='card4',
                                        className='info-card'),

                        dbc.Card([ dbc.CardHeader(avg_ratej_text),
                            dbc.CardBody([
                                                        dbc.Spinner([avg_ratej_indicator], size="lg",
                                                                    color="light",
                                                                    type="border", fullscreen=False,
                                                                    spinner_style=dict(marginTop=''))

                                                        ]) ]
                                          , style=dict(backgroundColor=indicator_bg_color,marginLeft='1vw'), id='card5',
                                          className='info-card'),

                        dbc.Card([dbc.CardHeader(avg_rateb_text),
                            dbc.CardBody([
                                                        dbc.Spinner([avg_rateb_indicator], size="lg",
                                                                    color="light",
                                                                    type="border", fullscreen=False,
                                                                    spinner_style=dict(marginTop=''))

                                                        ])]
                                          , style=dict(backgroundColor=indicator_bg_color,marginLeft='1vw'), id='card6',
                                          className='info-card'),

                       dbc.Card([dbc.CardHeader(avg_time_text),
                           dbc.CardBody([
                                                        dbc.Spinner([avg_time_indicator], size="lg",
                                                                    color="light",
                                                                    type="border", fullscreen=False,
                                                                    spinner_style=dict(marginTop=''))

                                                        ])]
                                          , style=dict(backgroundColor=indicator_bg_color,marginLeft='1vw'), id='card7',
                                          className='info-card'),

                            dbc.Card([dbc.CardHeader(to_be_paid_text),
                                dbc.CardBody([
                                                   dbc.Spinner([to_be_paid_indicator], size="lg",
                                                               color="light",
                                                               type="border", fullscreen=False,
                                                               spinner_style=dict(marginTop=''))

                                                   ])]
                                     , style=dict(backgroundColor=indicator_bg_color, marginLeft='1vw'), id='card8',
                                     className='info-card'),

                            dbc.Card([dbc.CardHeader(op_count_text),
                                dbc.CardBody([
                                                   dbc.Spinner([op_count_indicator], size="lg",
                                                               color="light",
                                                               type="border", fullscreen=False,
                                                               spinner_style=dict(marginTop=''))

                                                   ])]
                                     , style=dict(backgroundColor=indicator_bg_color, marginLeft='1vw'), id='card9',
                                     className='info-card')



                                           ],style=dict(display= 'flex', alignItems= 'center',
                                                        justifyContent= 'center',width='100%'))
                                            ]),
    html.Br(),
    dbc.Row([line_chart_col,hist_div_col,stacked_bar_chart_col,customer_table_col])
,html.Br(),html.Br()

]
,style=dict(backgroundColor=base_colors['color1'])
,className='main')


'''
-------- Backend Part --------
'''

# this function is responsible for downloading a pdf report with all the needed informations from dashboard when the pdf button is pressed
@app.callback(
    Output("pdf_output", "is_open"),
    [Input("download_pdf_button", "n_clicks")],
    [State("pdf_output", "is_open"),State('customer_table','data')
    ,State('customer_name_text','children'),State('sum_trans_indicator','figure'),State('sum_dep_indicator','figure'),
     State('avg_ratej_indicator','figure'),State('avg_rateb_indicator','figure'),State('avg_time_indicator','figure'),
     State('to_be_paid_indicator','figure'),State('op_count_indicator','figure')],
    prevent_initial_call=True)
def download_pdf(n, is_open,data,customer_name,trans_indicator,dep_indicator,ratej_indicator,rateb_indicator,
                 time_indicator,be_paid_indicator,operation_count_indicator):

    # getting the information needed from the dashboard info cards
    transactions_value=str(trans_indicator['data'][0]['value']) + ' R$'
    deposits_value=str(dep_indicator['data'][0]['value']) + ' R$'
    ratej_value=str( round(ratej_indicator['data'][0]['value'],1) )
    rateb_value=str( round(rateb_indicator['data'][0]['value'],1) )
    time_value=str(time_indicator['data'][0]['value']) + ' Months'
    be_paid_value=str(be_paid_indicator['data'][0]['value']) + ' R$'
    operations_value=str(operation_count_indicator['data'][0]['value'])

    # converting the table in the dashboard to a dataframe to be used in pdf file
    df_customer=pd.DataFrame(data)
    customer_id=df[df['ide']==df_customer['ide'][0]]['customer_id'].values[0]

    # creating a pdf file object
    pdf = FPDF(format='letter', unit='in')

    # calling the function ( in Functions.py) that use all the gathered info to generate the pdf file
    Functions.generate_pdf_report(df_customer,pdf,customer_name,customer_id,
                                  transactions_value,deposits_value,ratej_value,rateb_value,time_value,be_paid_value,operations_value)

    # returning a massage that confirms that the download was done succesfully
    return not is_open


# this function is responsible for downloading an excel file which contains all the original data filtered by only the customer id chosen
@app.callback(Output('download_excel', 'data'),
              Input('download_excel_button', 'n_clicks'),State('customer_table','data')

    ,prevent_initial_call=True)
def download_customer_data(clicks,data):
    # using the table in the dashboard to know which customer id was chosen
    temp_df=pd.DataFrame(data)
    selected_customer = df[df['ide'] == temp_df['ide'][0]]['customer_id'].values[0]

    # filtering the original dataframe based on the chosen customer id
    df_customer = dff[dff['customer_id'] == int(selected_customer)]
    df_customer['customer_id']=df_customer['customer_id'].astype(str)

    # sending the dataframe to the download component that handles the downloading process from the browser
    return send_data_frame(df_customer.to_excel, "{}.xlsx".format(selected_customer))


# this function is responsible for creating the table on the dashboard based on all filters chosen
@app.callback(Output('customer_table_div','children'),
              Input('apply_button','n_clicks'),
              [State('customer_id_menu','value'),State('banks_names_menu','value'),State('sectors_names_menu','value'),
               State('years_menu','value')]
            )
def update_table_card(clicks,selected_customer,selected_bank,selected_sector,selected_year):
    '''
    -------- Important --------

    all the functions starting from this one and all the bellow functions are triggered when the button called ( Apply Filters )
    is pressed and then we have 8 conditions to check for the filters values and the original
    dataframe is filtered depending on the existing condition , this filtering logic is repeated in all functions bellow
    and after the filtering happens the function that created the corresponding graph is called from ( Functions.py )
    '''


    if selected_sector=='All Sectors' and selected_bank=='All Banks' and selected_year=='All Years':
        df_customer = df[df['customer_id'] == selected_customer]

    elif selected_sector=='All Sectors' and selected_bank!='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['Year'] == selected_year)]

    elif selected_sector=='All Sectors' and selected_bank=='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['Year'] == selected_year)]

    elif selected_sector=='All Sectors' and selected_bank!='All Banks' and selected_year=='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) ]

    elif selected_sector!='All Sectors' and selected_bank=='All Banks' and selected_year=='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['sector_name4'] == selected_sector)]


    elif selected_sector!='All Sectors' and selected_bank=='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['Year'] == selected_year) & (df['sector_name4'] == selected_sector)]

    elif selected_sector != 'All Sectors' and selected_bank != 'All Banks' and selected_year == 'All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['sector_name4'] == selected_sector)]

    else:
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['sector_name4'] == selected_sector) & (df['Year'] == selected_year)]

    return Functions.get_customer_table(df_customer)


@app.callback(Output('stacked_bar_chart_div','children'),
              Input('apply_button','n_clicks'),
              [State('customer_id_menu','value'),State('banks_names_menu','value'),State('sectors_names_menu','value'),
               State('years_menu','value')]
            )
def update_stacked_bar_card(clicks,selected_customer,selected_bank,selected_sector,selected_year):
    if selected_sector=='All Sectors' and selected_bank=='All Banks' and selected_year=='All Years':
        df_customer = df[df['customer_id'] == selected_customer]

    elif selected_sector=='All Sectors' and selected_bank!='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['Year'] == selected_year)]

    elif selected_sector=='All Sectors' and selected_bank=='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['Year'] == selected_year)]

    elif selected_sector=='All Sectors' and selected_bank!='All Banks' and selected_year=='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) ]

    elif selected_sector!='All Sectors' and selected_bank=='All Banks' and selected_year=='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['sector_name4'] == selected_sector)]


    elif selected_sector!='All Sectors' and selected_bank=='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['Year'] == selected_year) & (df['sector_name4'] == selected_sector)]

    elif selected_sector != 'All Sectors' and selected_bank != 'All Banks' and selected_year == 'All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['sector_name4'] == selected_sector)]

    else:
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['sector_name4'] == selected_sector) & (df['Year'] == selected_year)]

    return Functions.get_stacked_bar_chart(df_customer)


@app.callback(Output('line_chart','figure'),
              Input('resolution_menu','value'),
              [State('customer_id_menu','value'),State('banks_names_menu','value'),
               State('sectors_names_menu','value'),State('years_menu','value')]
            ,prevent_initial_call=True)
def update_line_figure(selected_resolution,selected_customer,selected_bank,selected_sector,selected_year):
    if selected_sector=='All Sectors' and selected_bank=='All Banks' and selected_year=='All Years':
        df_customer = df[df['customer_id'] == selected_customer]

    elif selected_sector=='All Sectors' and selected_bank!='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['Year'] == selected_year)]

    elif selected_sector=='All Sectors' and selected_bank=='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['Year'] == selected_year)]

    elif selected_sector=='All Sectors' and selected_bank!='All Banks' and selected_year=='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) ]

    elif selected_sector!='All Sectors' and selected_bank=='All Banks' and selected_year=='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['sector_name4'] == selected_sector)]


    elif selected_sector!='All Sectors' and selected_bank=='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['Year'] == selected_year) & (df['sector_name4'] == selected_sector)]

    elif selected_sector != 'All Sectors' and selected_bank != 'All Banks' and selected_year == 'All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['sector_name4'] == selected_sector)]

    else:
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['sector_name4'] == selected_sector) & (df['Year'] == selected_year)]

    return Functions.get_line_chart(df_customer,selected_resolution)[1]


@app.callback(Output('line_chart_div','children'),
              Input('apply_button','n_clicks'),
              [State('customer_id_menu','value'),State('banks_names_menu','value'),
               State('sectors_names_menu','value'),State('years_menu','value'),State('resolution_menu','value')]
            )
def update_line_div(clicks,selected_customer,selected_bank,selected_sector,selected_year,selected_resolution):
    if selected_sector=='All Sectors' and selected_bank=='All Banks' and selected_year=='All Years':
        df_customer = df[df['customer_id'] == selected_customer]

    elif selected_sector=='All Sectors' and selected_bank!='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['Year'] == selected_year)]

    elif selected_sector=='All Sectors' and selected_bank=='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['Year'] == selected_year)]

    elif selected_sector=='All Sectors' and selected_bank!='All Banks' and selected_year=='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) ]

    elif selected_sector!='All Sectors' and selected_bank=='All Banks' and selected_year=='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['sector_name4'] == selected_sector)]


    elif selected_sector!='All Sectors' and selected_bank=='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['Year'] == selected_year) & (df['sector_name4'] == selected_sector)]

    elif selected_sector != 'All Sectors' and selected_bank != 'All Banks' and selected_year == 'All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['sector_name4'] == selected_sector)]

    else:
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['sector_name4'] == selected_sector) & (df['Year'] == selected_year)]

    return Functions.get_line_chart(df_customer,selected_resolution)[0]

@app.callback(Output('operations_hist_div','children'),
              Input('apply_button','n_clicks'),
              [State('customer_id_menu','value'),State('banks_names_menu','value'),State('sectors_names_menu','value'),
               State('years_menu','value')]
            )
def update_hist_card(clicks,selected_customer,selected_bank,selected_sector,selected_year):
    if selected_sector=='All Sectors' and selected_bank=='All Banks' and selected_year=='All Years':
        df_customer = df[df['customer_id'] == selected_customer]

    elif selected_sector=='All Sectors' and selected_bank!='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['Year'] == selected_year)]

    elif selected_sector=='All Sectors' and selected_bank=='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['Year'] == selected_year)]

    elif selected_sector=='All Sectors' and selected_bank!='All Banks' and selected_year=='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) ]

    elif selected_sector!='All Sectors' and selected_bank=='All Banks' and selected_year=='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['sector_name4'] == selected_sector)]


    elif selected_sector!='All Sectors' and selected_bank=='All Banks' and selected_year!='All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['Year'] == selected_year) & (df['sector_name4'] == selected_sector)]

    elif selected_sector != 'All Sectors' and selected_bank != 'All Banks' and selected_year == 'All Years':
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['sector_name4'] == selected_sector)]

    else:
        df_customer = df[(df['customer_id'] == selected_customer) & (df['bank_name'] == selected_bank) & (df['sector_name4'] == selected_sector) & (df['Year'] == selected_year)]

    return Functions.get_operations_hist(df_customer)




@app.callback([Output('sum_trans_indicator','figure'),Output('sum_dep_indicator','figure'),
               Output('avg_ratej_indicator','figure'),Output('avg_rateb_indicator','figure'),
               Output('avg_time_indicator','figure'),Output('to_be_paid_indicator','figure'),Output('op_count_indicator','figure'),
               Output('customer_name_text','children')],
              Input('apply_button','n_clicks'),
              [State('customer_id_menu','value'),State('banks_names_menu','value'),State('sectors_names_menu','value'),
               State('years_menu','value')]
            )
def update_indicators(clicks,selected_customer,selected_bank,selected_sector,selected_year):

    df_customer=df[df['customer_id'] == selected_customer]
    customer_name=df_customer['customer_name'].values[0]
    sum_trans_fig, sum_dep_fig, avg_ratej_fig, avg_rateb_fig, avg_time_fig, to_be_paid_fig, op_count_fig=Functions.get_indicators_figures(df_customer,selected_customer,selected_bank,selected_sector,selected_year)



    return (sum_trans_fig,sum_dep_fig,avg_ratej_fig,avg_rateb_fig,avg_time_fig,to_be_paid_fig,op_count_fig,customer_name)



# this function is responsible for changing the options in the different dropdowns menus depending on customer_id and other dropdowns values
@app.callback([Output('banks_names_menu','options'),Output('sectors_names_menu','options'),Output('years_menu','options'),
               Output('banks_names_menu','value'),Output('sectors_names_menu','value'),Output('years_menu','value')],
              [Input('customer_id_menu','value'),Input('banks_names_menu','value'),Input('sectors_names_menu','value')]
              ,prevent_initial_call=True)
def update_dropdowns(selected_customer,selected_bank,selected_sector):
    ctx = dash.callback_context
    input_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if input_id == 'customer_id_menu':
        customer_df = df[df['customer_id'] == selected_customer]

        banks_list = list(customer_df['bank_name'].unique())
        sectors_list = list(customer_df['sector_name4'].unique())
        customer_df['Year'] = (pd.DatetimeIndex(customer_df['approval_date']).year).astype(str)
        years = customer_df['Year'].to_list()
        years = list(OrderedDict.fromkeys(years))
        years.insert(0, 'All Years')
        banks_list.insert(0, 'All Banks')
        sectors_list.insert(0, 'All Sectors')

        return ([{'label': name, 'value': name} for name in banks_list] ,
                [{'label': name, 'value': name} for name in sectors_list],
                [{'label': year, 'value': year} for year in years],
                banks_list[0] , sectors_list[0],years[0] )


    elif input_id == 'sectors_names_menu':
        if selected_sector=='All Sectors':
            customer_df = df[ df['customer_id'] == selected_customer]

        else:
            customer_df = df[ (df['customer_id'] == selected_customer) & (df['sector_name4'] == selected_sector)]

        banks_list = list(customer_df['bank_name'].unique())
        sectors_list = list(customer_df['sector_name4'].unique())
        customer_df['Year'] = (pd.DatetimeIndex(customer_df['approval_date']).year).astype(str)
        years = customer_df['Year'].to_list()
        years = list(OrderedDict.fromkeys(years))
        years.insert(0, 'All Years')
        banks_list.insert(0, 'All Banks')
        sectors_list.insert(0, 'All Sectors')
        return ([{'label': name, 'value': name} for name in banks_list] ,
                dash.no_update,[{'label': year, 'value': year} for year in years],
                banks_list[0] , dash.no_update, years[0] )

    elif input_id == 'banks_names_menu':
        if selected_sector=='All Banks':
            customer_df = df[ df['customer_id'] == selected_customer]

        else:
            customer_df = df[ (df['customer_id'] == selected_customer) & (df['sector_name4'] == selected_sector) & (df['bank_name'] == selected_bank)]

        banks_list = list(customer_df['bank_name'].unique())
        sectors_list = list(customer_df['sector_name4'].unique())
        customer_df['Year'] = (pd.DatetimeIndex(customer_df['approval_date']).year).astype(str)
        years = customer_df['Year'].to_list()
        years = list(OrderedDict.fromkeys(years))
        years.insert(0, 'All Years')
        banks_list.insert(0, 'All Banks')
        sectors_list.insert(0, 'All Sectors')
        return (dash.no_update ,
                dash.no_update,[{'label': year, 'value': year} for year in years],
                dash.no_update , dash.no_update, years[0] )

    else:
        raise PreventUpdate

if __name__ == '__main__':
    app.run_server(host='localhost',port=8050,debug=False,dev_tools_silence_routes_logging=True)






