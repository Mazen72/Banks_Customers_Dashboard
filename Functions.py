import pandas as pd
import base64
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html , dash_table
from collections import OrderedDict
from fpdf import FPDF

base_colors={ 'color1': '#EBECF0', 'color2': '#F5F5F5','color3': '#0f70e0'}

indicator_size=22
indicator_text_color='white'
indicator_bg_color=base_colors['color3']
indicator_height=40

# generating the pdf report from the data got from the dashboard
def generate_pdf_report(df_customer,pdf,customer_name,customer_id,
                        transactions_value,deposits_value,ratej_value,rateb_value,time_value,be_paid_value,operations_value):

    df=df_customer[['ide','approval_date','transaction_value','deposited_value','sector_name4','bank_name']]
    df['approval_date']=df['approval_date'].astype(str)

    # adding the starting page to the pdf object
    pdf.add_page()

    # adjusting fonts , width of the pdf cells
    pdf.set_font('Times', '', 10.0)
    epw = pdf.w - 1 * pdf.l_margin
    col_width = epw / 7

    # creating an array of the dataframe rows to be used in the correct format the pdf object requires
    data = []
    for index, row in df.iterrows():
        data.append(row.to_list())

    data.insert(0,list(df.columns))

    # adding the first row in the pdf
    pdf.set_font('Times', 'B', 12.0)
    pdf.cell(epw, 0.0, 'Customer Name: {}  -  Customer ID: {}'.format(customer_name,customer_id), align='L')

    pdf.ln(0.5) # just giving space between rows

    # adding the second row in the pdf
    pdf.set_font('Times', 'B', 9.0)
    pdf.cell(epw, 0.0, 'Transactions Sum: {}  -  Deposits Sum: {}  -  Avg Jucas Rating: {}  -  Avg Bank Rating: {}'.format(
        transactions_value,deposits_value,ratej_value,rateb_value), align='L')

    pdf.ln(0.3)

    # adding the third row in the pdf
    pdf.set_font('Times', 'B', 9.0)
    pdf.cell(epw, 0.0, 'Avg Amortization Time: {}  -  To be Paid Sum: {}  -  Operations Count: {}'.format(
        time_value,be_paid_value,operations_value), align='L')

    # adding the datafrane as a table in the pdf
    pdf.set_font('Times', '', 8.0)
    pdf.ln(0.4)
    th = pdf.font_size
    for row in data:
        for datum in row:
            pdf.cell(col_width, 2 * th, str(datum), border=1,align='C')

        pdf.ln(2 * th)

    pdf.ln(4 * th)

    # downloading the pdf object as a pdf file in the app local directory
    pdf.output('{}.pdf'.format(customer_id), 'F')

# this function returns the filtered dataframe as a table object to be rendered in the dashboard
def get_customer_table(df_customer):
    df=df_customer[['ide','approval_date','transaction_value','deposited_value','sector_name4','bank_name']]
    df['approval_date']=df['approval_date'].astype(str)

    customer_table=dash_table.DataTable(
                id='customer_table',
                columns=[
                    {"name": i, "id": i} for i in df.columns
                ],
                data=df.to_dict("records"),filter_action='native',
                editable=False,  page_size=4,
                row_deletable=False,
        style_cell=dict(textAlign='center', border='1px solid black'
                        , backgroundColor='white', color='black', fontSize=14, fontWeight=''),
        style_header=dict(backgroundColor='#0f70e0', color='white',
                          fontWeight='bold', border='1px solid black', fontSize=14),
        style_table={'overflowX': 'auto', 'width': '100%', 'min-width': '100%','border':'1px solid black'}
            )


    return customer_table

# this function uses the filtered dataframe to generate the stacked bar chart
def get_stacked_bar_chart(df_customer):
    fig=go.Figure()
    color_list=px.colors.qualitative.D3
    banks_list = list(df_customer['bank_name'].unique())
    i=0
    for bank in banks_list:
        data=df_customer[df_customer['bank_name']==bank]
        data=data.groupby('sector_name4',sort=False)['ide'].count()
        data.sort_values(inplace=True, ascending=False)

        fig.add_trace(go.Bar(name=bank, x=data.index, y=data.astype('int64'),
                             marker_color=color_list[i],orientation='v',text=data.astype('int64'),
               textposition='auto', textfont=dict(
                #size=13,

            ))
                      )
        i+=1

    range_df=df_customer.groupby('sector_name4',sort=False)['ide'].count()
    range=range_df.astype('int64').max()
    fig.update_layout(title='<b>Customer Operations count<b>',title_x=0.5,
            xaxis_title='<b>Sector<b>', yaxis_title=None,
            # '<b>Topic<b>',
            font=dict(size=12, family='Arial', color='black'), hoverlabel=dict(
                font_size=14, font_family="Rockwell"), plot_bgcolor='white',
            paper_bgcolor='white', barmode='stack', margin=dict(l=0, r=0, t=40, b=0)
            ,yaxis=dict(range=[0,range])
        )
    fig.update_xaxes(showgrid=False, showline=True, zeroline=False, linecolor='black', visible=True)
    fig.update_yaxes(showgrid=False, showline=True, zeroline=False, linecolor='black',
                         visible=True, showticklabels=True)

    fig.update_traces(texttemplate = '<b>%{text}</b>')

    stacked_bar_chart_div = dcc.Graph(id='stacked_bar_chart', config={'displayModeBar': True, 'displaylogo': False,
                                              'modeBarButtonsToRemove': ['lasso2d', 'pan', 'zoom2d', 'zoomIn2d',
                                                                         'zoomOut2d', 'autoScale2d']}
                  , className='hist-fig',
                  style=dict(height='', backgroundColor='white', border=''), figure=fig
                  )
    return stacked_bar_chart_div

# this function uses the filtered dataframe to generate the line chart
def get_line_chart(df_customer,selected_resolution):
    df_customer.set_index('approval_date', inplace=True)
    graph_data = df_customer.resample('1M').sum()

    if selected_resolution == 'Sum Yearly':
        graph_data = df_customer.resample('1Y').sum()

    elif selected_resolution == 'Sum Quarterly':
        graph_data = df_customer.resample('3M').sum()


    elif selected_resolution == 'Sum Monthly':
        graph_data = df_customer.resample('1M').sum()

    elif selected_resolution == 'Sum Daily':
        graph_data = df_customer.resample('1D').sum()



    line_fig = go.Figure(go.Scatter())
    marker_mode='lines'
    if len(graph_data.index.unique()) ==1:
        marker_mode='markers'

    line_fig.add_trace(
        go.Scatter(x=graph_data.index, y=graph_data['transaction_value'].astype('int64'), mode=marker_mode, name='Transactions',
                   marker_color='#3B98F5'
                   # , stackgroup='one'
                   ))

    line_fig.add_trace(
        go.Scatter(x=graph_data.index, y=graph_data['deposited_value'].astype('int64'), mode=marker_mode, name='Deposits',
                   marker_color='#1500FF'
                   # , stackgroup='one'
                   ))

    line_fig.update_layout(title='<b>Operations Values Over Time<b>',
        xaxis_title='<b>Date<b>', yaxis_title='<b>Value (R$)<b>', title_x=0.5,
        font=dict(size=12, family='Arial', color='black'), hoverlabel=dict(
            font_size=16, font_family="Rockwell", font_color='white', bgcolor='black'), plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            rangeslider_visible=False
        ),margin=dict(l=0, r=0, t=30, b=0)
    )
    line_fig.update_xaxes(showgrid=False, showline=True, zeroline=False, linecolor='black')
    line_fig.update_yaxes(showgrid=False, showline=True, zeroline=False, linecolor='black')

    line_fig_div =dcc.Graph(id='line_chart',
                  config={'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToRemove': ['lasso2d', 'pan']},
                  className='date-fig',
                  style=dict(height='', backgroundColor='white', border=''), figure=line_fig
                  )

    return (line_fig_div,line_fig)

# this function uses the filtered dataframe to generate the histogram chart
def get_operations_hist(df_customer):


    hist_fig = go.Figure(go.Histogram())

    hist_fig.add_trace(go.Histogram(name='', x=df_customer['approval_date'].to_list(), showlegend=False,
                                    marker_color='#00bfff'))

    hist_fig.update_layout(
            title='<b>Distribution of Operations over Time<b>', xaxis_title='<b>Date<b>',title_x=0.5,
        yaxis_title='<b>Operations Count<b>',
        font=dict(size=12, family='Arial', color='black'), hoverlabel=dict(
            font_size=16, font_family="Rockwell", font_color='white', bgcolor='black'), plot_bgcolor='white',
        paper_bgcolor='white', margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(
            rangeslider_visible=True
        )

    )

    hist_fig.update_xaxes(showgrid=False, showline=True, zeroline=False, linecolor='black')
    hist_fig.update_yaxes(showgrid=False, showline=True, zeroline=False, linecolor='black')

    hist_div =dcc.Graph(id='operations_hist', config={'displayModeBar': True, 'scrollZoom': True, 'displaylogo': False,
                                                      'modeBarButtonsToRemove': ['zoom', 'pan','autoScale','lasso2d']},
                        className='hist-fig',
                  style=dict(height='', backgroundColor='white'), figure=hist_fig
                  )

    return hist_div

# this function uses the filtered dataframe to update all the information in cards
def get_indicators_figures(df_customer,selected_customer,selected_bank,selected_sector,selected_year):


    if selected_sector=='All Sectors' and selected_bank=='All Banks' and selected_year=='All Years':
        filtered_trans_value=int(df_customer['transaction_value'].sum())
        filtered_dep_value = int(df_customer['deposited_value'].sum())
        filtered_ratej_value = df_customer['rate_JUCAS'].mean()
        filtered_rateb_value = df_customer['rate_bank'].mean()
        filtered_time_amor_value = int(df_customer['time_amortization'].mean())
        to_be_paid_value = int(df_customer['to_be_paid'].sum())
        op_count_value = int(df_customer['ide'].count())



    elif selected_sector == 'All Sectors' and selected_bank != 'All Banks' and selected_year != 'All Years':
        groupby_list=['bank_name','Year']
        customer_sum_tans_df = df_customer.groupby(groupby_list)['transaction_value'].sum().reset_index()
        customer_sum_dep_df = df_customer.groupby(groupby_list)['deposited_value'].sum().reset_index()
        customer_avg_ratej_df = df_customer.groupby(groupby_list)['rate_JUCAS'].mean().reset_index()
        customer_avg_rateb_df = df_customer.groupby(groupby_list)['rate_bank'].mean().reset_index()
        customer_time_amor_df = df_customer.groupby(groupby_list)['time_amortization'].mean().reset_index()
        to_be_paid_df = df_customer.groupby(groupby_list)['to_be_paid'].sum().reset_index()
        op_count_df = df_customer.groupby(groupby_list)['ide'].count().reset_index()


        filtered_trans_value = customer_sum_tans_df[(customer_sum_tans_df['bank_name'] == selected_bank) &
                                                    (customer_sum_tans_df['Year'] == selected_year)]
        filtered_trans_value = int(filtered_trans_value['transaction_value'].values[0])

        filtered_dep_value = customer_sum_dep_df[(customer_sum_dep_df['bank_name'] == selected_bank) &
                                                    (customer_sum_dep_df['Year'] == selected_year)]
        filtered_dep_value = int(filtered_dep_value['deposited_value'].values[0])

        filtered_ratej_value = customer_avg_ratej_df[(customer_avg_ratej_df['bank_name'] == selected_bank) &
                                                    (customer_avg_ratej_df['Year'] == selected_year)]
        filtered_ratej_value = filtered_ratej_value['rate_JUCAS'].values[0]

        filtered_rateb_value = customer_avg_rateb_df[(customer_avg_rateb_df['bank_name'] == selected_bank) &
                                                    (customer_avg_rateb_df['Year'] == selected_year)]
        filtered_rateb_value = filtered_rateb_value['rate_bank'].values[0]

        filtered_time_amor_value = customer_time_amor_df[(customer_time_amor_df['bank_name'] == selected_bank) &
                                                    (customer_time_amor_df['Year'] == selected_year)]
        filtered_time_amor_value = int(filtered_time_amor_value['time_amortization'].values[0])

        to_be_paid_value = to_be_paid_df[(to_be_paid_df['bank_name'] == selected_bank) &
                                                    (to_be_paid_df['Year'] == selected_year)]
        to_be_paid_value = int(to_be_paid_value['to_be_paid'].values[0])

        op_count_value = op_count_df[(op_count_df['bank_name'] == selected_bank) &
                                                    (op_count_df['Year'] == selected_year)]
        op_count_value = int(op_count_value['ide'].values[0])

    elif selected_sector == 'All Sectors' and selected_bank == 'All Banks' and selected_year != 'All Years':
        groupby_list=['Year']
        customer_sum_tans_df = df_customer.groupby(groupby_list)['transaction_value'].sum().reset_index()
        customer_sum_dep_df = df_customer.groupby(groupby_list)['deposited_value'].sum().reset_index()
        customer_avg_ratej_df = df_customer.groupby(groupby_list)['rate_JUCAS'].mean().reset_index()
        customer_avg_rateb_df = df_customer.groupby(groupby_list)['rate_bank'].mean().reset_index()
        customer_time_amor_df = df_customer.groupby(groupby_list)['time_amortization'].mean().reset_index()
        to_be_paid_df = df_customer.groupby(groupby_list)['to_be_paid'].sum().reset_index()
        op_count_df = df_customer.groupby(groupby_list)['ide'].count().reset_index()


        filtered_trans_value = customer_sum_tans_df[
                                                    (customer_sum_tans_df['Year'] == selected_year)]
        filtered_trans_value = int(filtered_trans_value['transaction_value'].values[0])

        filtered_dep_value = customer_sum_dep_df[
                                                    (customer_sum_dep_df['Year'] == selected_year)]
        filtered_dep_value = int(filtered_dep_value['deposited_value'].values[0])

        filtered_ratej_value = customer_avg_ratej_df[
                                                    (customer_avg_ratej_df['Year'] == selected_year)]
        filtered_ratej_value = filtered_ratej_value['rate_JUCAS'].values[0]

        filtered_rateb_value = customer_avg_rateb_df[
                                                    (customer_avg_rateb_df['Year'] == selected_year)]
        filtered_rateb_value = filtered_rateb_value['rate_bank'].values[0]

        filtered_time_amor_value = customer_time_amor_df[
                                                    (customer_time_amor_df['Year'] == selected_year)]
        filtered_time_amor_value = int(filtered_time_amor_value['time_amortization'].values[0])

        to_be_paid_value = to_be_paid_df[
                                                    (to_be_paid_df['Year'] == selected_year)]
        to_be_paid_value = int(to_be_paid_value['to_be_paid'].values[0])

        op_count_value = op_count_df[
                                                    (op_count_df['Year'] == selected_year)]
        op_count_value = int(op_count_value['ide'].values[0])

    elif selected_sector == 'All Sectors' and selected_bank != 'All Banks' and selected_year == 'All Years':
        groupby_list=['bank_name']
        customer_sum_tans_df = df_customer.groupby(groupby_list)['transaction_value'].sum().reset_index()
        customer_sum_dep_df = df_customer.groupby(groupby_list)['deposited_value'].sum().reset_index()
        customer_avg_ratej_df = df_customer.groupby(groupby_list)['rate_JUCAS'].mean().reset_index()
        customer_avg_rateb_df = df_customer.groupby(groupby_list)['rate_bank'].mean().reset_index()
        customer_time_amor_df = df_customer.groupby(groupby_list)['time_amortization'].mean().reset_index()
        to_be_paid_df = df_customer.groupby(groupby_list)['to_be_paid'].sum().reset_index()
        op_count_df = df_customer.groupby(groupby_list)['ide'].count().reset_index()


        filtered_trans_value = customer_sum_tans_df[(customer_sum_tans_df['bank_name'] == selected_bank)]
        filtered_trans_value = int(filtered_trans_value['transaction_value'].values[0])

        filtered_dep_value = customer_sum_dep_df[(customer_sum_dep_df['bank_name'] == selected_bank) ]
        filtered_dep_value = int(filtered_dep_value['deposited_value'].values[0])

        filtered_ratej_value = customer_avg_ratej_df[(customer_avg_ratej_df['bank_name'] == selected_bank) ]
        filtered_ratej_value = filtered_ratej_value['rate_JUCAS'].values[0]

        filtered_rateb_value = customer_avg_rateb_df[(customer_avg_rateb_df['bank_name'] == selected_bank) ]
        filtered_rateb_value = filtered_rateb_value['rate_bank'].values[0]

        filtered_time_amor_value = customer_time_amor_df[(customer_time_amor_df['bank_name'] == selected_bank) ]
        filtered_time_amor_value = int(filtered_time_amor_value['time_amortization'].values[0])

        to_be_paid_value = to_be_paid_df[(to_be_paid_df['bank_name'] == selected_bank) ]
        to_be_paid_value = int(to_be_paid_value['to_be_paid'].values[0])

        op_count_value = op_count_df[(op_count_df['bank_name'] == selected_bank) ]
        op_count_value = int(op_count_value['ide'].values[0])

    elif selected_sector != 'All Sectors' and selected_bank == 'All Banks' and selected_year == 'All Years':
        groupby_list=['sector_name4']
        customer_sum_tans_df = df_customer.groupby(groupby_list)['transaction_value'].sum().reset_index()
        customer_sum_dep_df = df_customer.groupby(groupby_list)['deposited_value'].sum().reset_index()
        customer_avg_ratej_df = df_customer.groupby(groupby_list)['rate_JUCAS'].mean().reset_index()
        customer_avg_rateb_df = df_customer.groupby(groupby_list)['rate_bank'].mean().reset_index()
        customer_time_amor_df = df_customer.groupby(groupby_list)['time_amortization'].mean().reset_index()
        to_be_paid_df = df_customer.groupby(groupby_list)['to_be_paid'].sum().reset_index()
        op_count_df = df_customer.groupby(groupby_list)['ide'].count().reset_index()


        filtered_trans_value = customer_sum_tans_df[(customer_sum_tans_df['sector_name4'] == selected_sector)]
        filtered_trans_value = int(filtered_trans_value['transaction_value'].values[0])

        filtered_dep_value = customer_sum_dep_df[(customer_sum_dep_df['sector_name4'] == selected_sector) ]
        filtered_dep_value = int(filtered_dep_value['deposited_value'].values[0])

        filtered_ratej_value = customer_avg_ratej_df[(customer_avg_ratej_df['sector_name4'] == selected_sector) ]
        filtered_ratej_value = filtered_ratej_value['rate_JUCAS'].values[0]

        filtered_rateb_value = customer_avg_rateb_df[(customer_avg_rateb_df['sector_name4'] == selected_sector) ]
        filtered_rateb_value = filtered_rateb_value['rate_bank'].values[0]

        filtered_time_amor_value = customer_time_amor_df[(customer_time_amor_df['sector_name4'] == selected_sector) ]
        filtered_time_amor_value = int(filtered_time_amor_value['time_amortization'].values[0])

        to_be_paid_value = to_be_paid_df[(to_be_paid_df['sector_name4'] == selected_sector) ]
        to_be_paid_value = int(to_be_paid_value['to_be_paid'].values[0])

        op_count_value = op_count_df[(op_count_df['sector_name4'] == selected_sector) ]
        op_count_value = int(op_count_value['ide'].values[0])

    elif selected_sector != 'All Sectors' and selected_bank == 'All Banks' and selected_year != 'All Years':
        groupby_list=['sector_name4','Year']
        customer_sum_tans_df = df_customer.groupby(groupby_list)['transaction_value'].sum().reset_index()
        customer_sum_dep_df = df_customer.groupby(groupby_list)['deposited_value'].sum().reset_index()
        customer_avg_ratej_df = df_customer.groupby(groupby_list)['rate_JUCAS'].mean().reset_index()
        customer_avg_rateb_df = df_customer.groupby(groupby_list)['rate_bank'].mean().reset_index()
        customer_time_amor_df = df_customer.groupby(groupby_list)['time_amortization'].mean().reset_index()
        to_be_paid_df = df_customer.groupby(groupby_list)['to_be_paid'].sum().reset_index()
        op_count_df = df_customer.groupby(groupby_list)['ide'].count().reset_index()


        filtered_trans_value = customer_sum_tans_df[(customer_sum_tans_df['sector_name4'] == selected_sector) &
                                                    (customer_sum_tans_df['Year'] == selected_year)]
        filtered_trans_value = int(filtered_trans_value['transaction_value'].values[0])

        filtered_dep_value = customer_sum_dep_df[(customer_sum_dep_df['sector_name4'] == selected_sector) &
                                                    (customer_sum_dep_df['Year'] == selected_year)]
        filtered_dep_value = int(filtered_dep_value['deposited_value'].values[0])

        filtered_ratej_value = customer_avg_ratej_df[(customer_avg_ratej_df['sector_name4'] == selected_sector) &
                                                    (customer_avg_ratej_df['Year'] == selected_year)]
        filtered_ratej_value = filtered_ratej_value['rate_JUCAS'].values[0]

        filtered_rateb_value = customer_avg_rateb_df[(customer_avg_rateb_df['sector_name4'] == selected_sector) &
                                                    (customer_avg_rateb_df['Year'] == selected_year)]
        filtered_rateb_value = filtered_rateb_value['rate_bank'].values[0]

        filtered_time_amor_value = customer_time_amor_df[(customer_time_amor_df['sector_name4'] == selected_sector) &
                                                    (customer_time_amor_df['Year'] == selected_year)]
        filtered_time_amor_value = int(filtered_time_amor_value['time_amortization'].values[0])

        to_be_paid_value = to_be_paid_df[(to_be_paid_df['sector_name4'] == selected_sector) &
                                                    (to_be_paid_df['Year'] == selected_year)]
        to_be_paid_value = int(to_be_paid_value['to_be_paid'].values[0])

        op_count_value = op_count_df[(op_count_df['sector_name4'] == selected_sector) &
                                                    (op_count_df['Year'] == selected_year)]
        op_count_value = int(op_count_value['ide'].values[0])

    elif selected_sector != 'All Sectors' and selected_bank != 'All Banks' and selected_year == 'All Years':
        groupby_list = ['bank_name', 'sector_name4']
        customer_sum_tans_df = df_customer.groupby(groupby_list)['transaction_value'].sum().reset_index()
        customer_sum_dep_df = df_customer.groupby(groupby_list)['deposited_value'].sum().reset_index()
        customer_avg_ratej_df = df_customer.groupby(groupby_list)['rate_JUCAS'].mean().reset_index()
        customer_avg_rateb_df = df_customer.groupby(groupby_list)['rate_bank'].mean().reset_index()
        customer_time_amor_df = df_customer.groupby(groupby_list)['time_amortization'].mean().reset_index()
        to_be_paid_df = df_customer.groupby(groupby_list)['to_be_paid'].sum().reset_index()
        op_count_df = df_customer.groupby(groupby_list)['ide'].count().reset_index()

        filtered_trans_value = customer_sum_tans_df[(customer_sum_tans_df['bank_name'] == selected_bank) &
                                                    (customer_sum_tans_df['sector_name4'] == selected_year)]
        filtered_trans_value = int(filtered_trans_value['transaction_value'].values[0])

        filtered_dep_value = customer_sum_dep_df[(customer_sum_dep_df['bank_name'] == selected_bank) &
                                                 (customer_sum_dep_df['sector_name4'] == selected_sector)]
        filtered_dep_value = int(filtered_dep_value['deposited_value'].values[0])

        filtered_ratej_value = customer_avg_ratej_df[(customer_avg_ratej_df['bank_name'] == selected_bank) &
                                                     (customer_avg_ratej_df['sector_name4'] == selected_sector)]
        filtered_ratej_value = filtered_ratej_value['rate_JUCAS'].values[0]

        filtered_rateb_value = customer_avg_rateb_df[(customer_avg_rateb_df['bank_name'] == selected_bank) &
                                                     (customer_avg_rateb_df['sector_name4'] == selected_sector)]
        filtered_rateb_value = filtered_rateb_value['rate_bank'].values[0]

        filtered_time_amor_value = customer_time_amor_df[(customer_time_amor_df['bank_name'] == selected_bank) &
                                                         (customer_time_amor_df['sector_name4'] == selected_sector)]
        filtered_time_amor_value = int(filtered_time_amor_value['time_amortization'].values[0])

        to_be_paid_value = to_be_paid_df[(to_be_paid_df['bank_name'] == selected_bank) &
                                         (to_be_paid_df['sector_name4'] == selected_sector)]
        to_be_paid_value = int(to_be_paid_value['to_be_paid'].values[0])

        op_count_value = op_count_df[(op_count_df['bank_name'] == selected_bank) &
                                     (op_count_df['sector_name4'] == selected_sector)]
        op_count_value = int(op_count_value['ide'].values[0])

    else:
        groupby_list = ['bank_name', 'sector_name4','Year']
        customer_sum_tans_df = df_customer.groupby(groupby_list)['transaction_value'].sum().reset_index()
        customer_sum_dep_df = df_customer.groupby(groupby_list)['deposited_value'].sum().reset_index()
        customer_avg_ratej_df = df_customer.groupby(groupby_list)['rate_JUCAS'].mean().reset_index()
        customer_avg_rateb_df = df_customer.groupby(groupby_list)['rate_bank'].mean().reset_index()
        customer_time_amor_df = df_customer.groupby(groupby_list)['time_amortization'].mean().reset_index()
        to_be_paid_df = df_customer.groupby(groupby_list)['to_be_paid'].sum().reset_index()
        op_count_df = df_customer.groupby(groupby_list)['ide'].count().reset_index()

        filtered_trans_value = customer_sum_tans_df[(customer_sum_tans_df['bank_name'] == selected_bank) &
                                                    (customer_sum_tans_df['sector_name4'] == selected_year) & (customer_sum_tans_df['Year'] == selected_year)]
        filtered_trans_value = int(filtered_trans_value['transaction_value'].values[0])

        filtered_dep_value = customer_sum_dep_df[(customer_sum_dep_df['bank_name'] == selected_bank) &
                                                 (customer_sum_dep_df['sector_name4'] == selected_sector) & (customer_sum_dep_df['Year'] == selected_year)]
        filtered_dep_value = int(filtered_dep_value['deposited_value'].values[0])

        filtered_ratej_value = customer_avg_ratej_df[(customer_avg_ratej_df['bank_name'] == selected_bank) &
                                                     (customer_avg_ratej_df['sector_name4'] == selected_sector) & (customer_avg_ratej_df['Year'] == selected_year)]
        filtered_ratej_value = filtered_ratej_value['rate_JUCAS'].values[0]

        filtered_rateb_value = customer_avg_rateb_df[(customer_avg_rateb_df['bank_name'] == selected_bank) &
                                                     (customer_avg_rateb_df['sector_name4'] == selected_sector) & (customer_avg_rateb_df['Year'] == selected_year)]
        filtered_rateb_value = filtered_rateb_value['rate_bank'].values[0]

        filtered_time_amor_value = customer_time_amor_df[(customer_time_amor_df['bank_name'] == selected_bank) &
                                                         (customer_time_amor_df['sector_name4'] == selected_sector) & (customer_time_amor_df['Year'] == selected_year)]
        filtered_time_amor_value = int(filtered_time_amor_value['time_amortization'].values[0])

        to_be_paid_value = to_be_paid_df[(to_be_paid_df['bank_name'] == selected_bank) &
                                         (to_be_paid_df['sector_name4'] == selected_sector) & (to_be_paid_df['Year'] == selected_year)]
        to_be_paid_value = int(to_be_paid_value['to_be_paid'].values[0])

        op_count_value = op_count_df[(op_count_df['bank_name'] == selected_bank) &
                                     (op_count_df['sector_name4'] == selected_sector) & (op_count_df['Year'] == selected_year)]
        op_count_value = int(op_count_value['ide'].values[0])






    sum_trans_fig = go.Figure()

    sum_trans_fig.add_trace(go.Indicator(
        mode="number",
        value=filtered_trans_value,
        number={'font': {'color': indicator_text_color, 'size': indicator_size}, 'suffix': " R$", 'valueformat': ","},
        domain={'row': 0, 'column': 0}
    ))

    sum_trans_fig.update_layout(paper_bgcolor=indicator_bg_color, plot_bgcolor='white',
                                height=indicator_height, margin=dict(l=0, r=0, t=0, b=0),

                                )

    sum_dep_fig = go.Figure()

    sum_dep_fig.add_trace(go.Indicator(
        mode="number",
        value=filtered_dep_value,
        number={'font': {'color': indicator_text_color, 'size': indicator_size}, 'suffix': " R$", 'valueformat': ","},
        domain={'row': 0, 'column': 0}
    ))

    sum_dep_fig.update_layout(paper_bgcolor=indicator_bg_color, plot_bgcolor='white',
                              height=indicator_height, margin=dict(l=0, r=0, t=0, b=0),

                              )

    avg_ratej_fig = go.Figure()

    avg_ratej_fig.add_trace(go.Indicator(
        mode="number",
        value=filtered_ratej_value,
        number={'font': {'color': indicator_text_color, 'size': indicator_size}},
        domain={'row': 0, 'column': 0}
    ))

    avg_ratej_fig.update_layout(paper_bgcolor=indicator_bg_color, plot_bgcolor='white',
                                height=indicator_height, margin=dict(l=0, r=0, t=0, b=0),

                                )


    avg_rateb_fig = go.Figure()

    avg_rateb_fig.add_trace(go.Indicator(
        mode="number",
        value=filtered_rateb_value,
        number={'font': {'color': indicator_text_color, 'size': indicator_size}},
        domain={'row': 0, 'column': 0}
    ))

    avg_rateb_fig.update_layout(paper_bgcolor=indicator_bg_color, plot_bgcolor='white',
                                height=indicator_height, margin=dict(l=0, r=0, t=0, b=0),

                                )

    avg_time_fig = go.Figure()

    avg_time_fig.add_trace(go.Indicator(
        mode="number",
        value=filtered_time_amor_value,
        number={'font': {'color': indicator_text_color, 'size': indicator_size}, 'suffix': " Months"},
        domain={'row': 0, 'column': 0}
    ))

    avg_time_fig.update_layout(paper_bgcolor=indicator_bg_color, plot_bgcolor='white',
                               height=indicator_height, margin=dict(l=0, r=0, t=0, b=0),

                               )

    to_be_paid_fig = go.Figure()

    to_be_paid_fig.add_trace(go.Indicator(
        mode="number",
        value=to_be_paid_value,
        number={'font': {'color': indicator_text_color, 'size': indicator_size}, 'suffix': " R$", 'valueformat': ","},
        domain={'row': 0, 'column': 0}
    ))

    to_be_paid_fig.update_layout(paper_bgcolor=indicator_bg_color, plot_bgcolor='white',
                                 height=indicator_height, margin=dict(l=0, r=0, t=0, b=0),

                                 )

    op_count_fig = go.Figure()

    op_count_fig.add_trace(go.Indicator(
        mode="number",
        value=op_count_value,
        number={'font': {'color': indicator_text_color, 'size': indicator_size}},
        domain={'row': 0, 'column': 0}
    ))

    op_count_fig.update_layout(paper_bgcolor=indicator_bg_color, plot_bgcolor='white',
                               height=indicator_height, margin=dict(l=0, r=0, t=0, b=0),

                               )

    return (sum_trans_fig,sum_dep_fig,avg_ratej_fig,avg_rateb_fig,avg_time_fig,to_be_paid_fig,op_count_fig)

