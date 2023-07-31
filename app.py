import streamlit as st
import yfinance as yf 
import datetime 
import pandas as pd 
import matplotlib.pyplot as plt 
import numpy as np 
from finta import TA

yf.pdr_override()

def app():
    st.write("""#Dashboard""")

    st.sidebar.header("EnterTicker and date as below")

    today = datetime.date.today()

    def user_input_feature():
        ticker = st.sidebar.text_input("Ticker", 'AAPL')
        start_date = st.sidebar.text_input("Start Date","2022-01-01")
        end_date = st.sidebar.text_input("End Date",f'{today}')
        return ticker, start_date, end_date

    symbol, start,end = user_input_feature()

    company_name = symbol
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)

    #read data
    data = yf.download(symbol, start, end)
    #["open", "high", "low", "close"]
    ohlc = data.rename(columns={"Open": "open", "Close": "close","High":"high","Low":"low"})
    #adjust close price
    st.header(f"Adjusted close price\n {company_name}")

    #initialize position column for buy / sell signal
    data['Position'] = 0

    # support and resistance lines
    data = data[(data['High']>=0) & (data['Low']>=0)]
    data['SR_Range'] = data['High'] - data['Low']
    data['SR_Ratio'] = ((data['Adj Close']-data['Low'])/data['SR_Range'])
    data['SR_Support']= data['Adj Close'] - data['SR_Ratio'] * data['SR_Range']
    data['SR_Resistance'] = data['SR_Support'] +data['SR_Range']

    #Trend line
    data['Trend'] = TA.SMA(ohlc, 50)

    data['VCP']= 0
    for i in range(20, len(data['VCP'])):
        volume_sum = sum(data['Volume'][i-20:i])
        price_volume_sum = sum(data['Volume'][i-20:i] * data['Adj Close'][i-20:i])
        vwap_20 = price_volume_sum / volume_sum
        if data['Adj Close'][i]>vwap_20:
            data['VCP'][i]=1
        else:
            data['VCP'][i]=-1

    #condition for buy signal
    data['Avg_Volume'] = data['Volume'].rolling(window =30).mean()
    data['Close_to_support'] = (data['Adj Close'] - data['SR_Support'] )/ data['Adj Close']
    data['Buy_Signal'] =0 
    data.loc[(data['VCP']==1)&(data['Volume']>data['Avg_Volume'])&(data['Close_to_support']<0.05),'Buy_Signal']=1

    #claculate 3-day and 50day exponential moving averages
    data['EMA_3'] = TA.EMA(ohlc,3)
    data['EMA_50'] = TA.EMA(ohlc,50)

    #set sell signal when EMA_3 is below EMA_50
    data['Sell_Signal'] = np.where(data['EMA_3']< data['EMA_50'],1,0)

    #set position column based on buy and sell signals
    for i in range(1, len(data)):
        if data['Buy_Signal'][i]==1:
            data['Position'][i] =1
        elif data['Sell_Signal'] [i]==1:
            data['Position'][i] =0
        else:
            data['Position'][i] = data['Position'][i-1]

    #calculate daliy returns
    data['Returns'] = data['Adj Close'].pct_change()

    #calculate cumulative returns
    data['Cumulative_Returns'] = (1+ data['Returns']).cumprod()

    #plot closing price with buy and sell signal, and support and resistance lines
    fig, ax = plt.subplots()
    ax.plot(data.index, data['Adj Close'],label ='Closing Price')
    ax.scatter(data[data['Buy_Signal']==1].index,data[data['Buy_Signal']==1]['Adj Close'], color ='green',marker='^',label = 'Buy_Signal')
    ax.scatter(data[data['Sell_Signal']==1].index,data[data['Sell_Signal']==1]['Adj Close'], color ='red',marker='v',label = 'Sell_Signal')
    ax.plot(data.index, data['SR_Support'],color='orange',label='Support Line')
    ax.plot(data.index, data['SR_Resistance'],color='red',label='Resistance Line')
    plt.xticks(rotation=45)
    plt.title(f"{company_name} Closing Price with Buy/Sell Signals and support/resistance line")
    plt.xlabel("Date")
    plt.ylabel("Price ($)")
    #plt.legend
    st.pyplot(fig)

    #plot cumulative returns
    st.header(f"cumulative returns\n{company_name}")
    st.line_chart(data['Cumulative_Returns'])

if __name__ == '__main__':
    app()

