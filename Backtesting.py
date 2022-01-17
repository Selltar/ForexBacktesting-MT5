import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import pytz
import talib

# display data on the MetaTrader 5 package
print("MetaTrader5 package author: ", mt5.__author__)
print("MetaTrader5 package version: ", mt5.__version__)

print("Connecting.....")

# establish MetaTrader 5 connection to a specified trading account
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()
else:
    print("Connection Successful")

timezone = pytz.timezone("Etc/UTC")  # set time zone to UTC
Currency = "AUDUSD"

Capital = 500
InitialCapital = Capital
Timeframe = mt5.TIMEFRAME_M5  # data frequency/internval (eg. minutes, hourly, daily...etc)
Startdate = datetime(2022, 1, 7,
                     tzinfo=timezone)  # create 'datetime' object in UTC time zone to avoid the implementation of a local time zone offset
AmountOfCandlesPerMonth = 5760
# 5M = 5760
# 15M = 1920
# 30M = 960
NumberOfMonths = 2
TimePeriod = AmountOfCandlesPerMonth * NumberOfMonths  # amount of data sets of your specified timeframe

print("Retrieving Data From MT5 Platform......")
# get data starting from specified dates in UTC time zone
rates = mt5.copy_rates_from(Currency, Timeframe, Startdate, TimePeriod)

mt5.shutdown()  # shut down connection to the MetaTrader 5 terminal

pd.set_option('display.max_columns', 30)  # number of columns to be displayed
pd.set_option('display.width', 500)  # max table width to display

# create DataFrame out of the obtained data
data = pd.DataFrame(rates)
data['close'] = data['close'].astype(float)
data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Tick_volume', 'Spread', 'Real_volume']

# extracting time from date dataset
data.insert(5, "Time", data['Date'], True)

# convert time in seconds into the datetime format
data['Time'] = pd.to_datetime(data['Time'], unit='s')

# display data
print(data)
print(len(data))
print(data['Time'][0], data['Time'][100], data['Time'][len(data) - 1])

# change df values to list
Date = data['Date'].values
Time = data['Time'].values
OpenPrice = data['Open'].values
HighPrice = data['High'].values
LowPrice = data['Low'].values
ClosePrice = data['Close'].values
Spread = data['Spread'].values
TickVolume = data['Tick_volume'].values
RealVolume = data['Real_volume'].values

print("Applying Indicators.....")
# Momentum
Momentum = talib.MOM(ClosePrice, timeperiod=1)

# Average True Range
ATR = talib.ATR(HighPrice, LowPrice, ClosePrice, timeperiod=10)

# Keltner Channel
KeltnerMiddleLine = talib.EMA(ClosePrice, timeperiod=20)
KeltnerUpperBand = KeltnerMiddleLine + 1 * ATR
KeltnerLowerBand = KeltnerMiddleLine - 1 * ATR

# Stochastic Oscillator
slowk, slowd = talib.STOCH(HighPrice, LowPrice, ClosePrice, fastk_period=14, slowk_period=3, slowk_matype=0,
                           slowd_period=3, slowd_matype=0)

# Trade results and signal storage
WinResultList = []
LossResultList = []
SignalList = []


class Results:
    def __init__(self, result, dateandtime, closeprice, openprice, volume):
        self.result = result
        self.dateandtime = dateandtime
        self.closeprice = closeprice
        self.openprice = openprice
        self.volume = volume

    def get_result(self):
        return self.result

    def get_dateandtime(self):
        return self.dateandtime

    def get_closeprice(self):
        return self.closeprice

    def get_openprice(self):
        return self.openprice

    def get_volume(self):
        return self.volume


class Signals:
    def __init__(self, direction, dateandtime, closeprice, openprice, volume):
        self.direction = direction
        self.dateandtime = dateandtime
        self.closeprice = closeprice
        self.openprice = openprice
        self.volume = volume

    def get_direction(self):
        return self.direction

    def get_dateandtime(self):
        return self.dateandtime

    def get_closeprice(self):
        return self.closeprice

    def get_openprice(self):
        return self.openprice

    def get_volume(self):
        return self.volume


print("Begin Backtesting Simulation.....")
for i in range(len(data)):
    SignalPresent = ''
    BuyingOrSelling = ''

    #Get the hour of the day
    DateAndTimeFromString = Time[i]
    TimeCountString = str(DateAndTimeFromString)
    WINTimeCount = TimeCountString.split("T")
    FinalTimeCount = WINTimeCount[1]
    FinalTimeCount = FinalTimeCount.replace("'", "")
    FinalTimeCount = FinalTimeCount.replace("]", "")
    FinalTimeCountString = str(FinalTimeCount)
    WINTimeCountTwo = FinalTimeCountString.split(':')
    FinalTimeCount = WINTimeCountTwo[0]

    FinalTimeCountInt = int(FinalTimeCount)


    if FinalTimeCountInt >= 10 and FinalTimeCountInt < 17:  # Trade signals between 10AM - 5PM

        # BUY Strategy = If Stochastic OScillator is below the lower band and Keltner Channel is outside the Lower band
        # expect a reversal and BUY
        if slowk[i] < 20 and slowd[i] < 20 and \
           slowk[i - 1] < slowd[i - 1] and slowk[i] > slowd[i] and \
           ClosePrice[i] < KeltnerLowerBand[i]:

            SignalPresent = 'YES'
            BuyingOrSelling = 'BUY'

            SignalV = Signals(BuyingOrSelling, Time[i], ClosePrice[i], OpenPrice[i], TickVolume[i])
            SignalList.append(SignalV)

        # SELL Strategy = If Stochastic OScillator is above the upper band and Keltner Channel is outside the Upper band
        # expect a reversal and SELL
        elif slowk[i] > 80 and slowd[i] > 80 and \
             slowk[i - 1] > slowd[i - 1] and slowk[i] < slowd[i] and \
             ClosePrice[i] > KeltnerUpperBand[i]:

            SignalPresent = 'YES'
            BuyingOrSelling = 'SELL'

            SignalV = Signals(BuyingOrSelling, Time[i], ClosePrice[i], OpenPrice[i], TickVolume[i])
            SignalList.append(SignalV)

        else:
            BuyingOrSelling = ''
            SignalPresent = ''

        if SignalPresent == "YES":

            for j in range(1):

                if Capital <= 0:
                    break

                # Set StopLoss and TakeProfit
                StopLossPips = 0.0007
                PipLossValue = StopLossPips / 0.0001
                TakeProfitPips = 0.0014
                PipWinValue = TakeProfitPips / 0.0001
                SpreadValue = Spread[i] * 0.00001

                PipValue = 2
                MainPipValue = 2
                lotsize = 1.0
                if BuyingOrSelling == "BUY":

                    # check the next 500 candles
                    for Candle in range(500):

                        if Candle == 0:
                            Candle = i + 1
                        else:
                            Candle = i + Candle

                        AskPrice = ClosePrice[i] + SpreadValue
                        TakeProfitBUY = AskPrice + TakeProfitPips
                        StopLossPointBUY = AskPrice - StopLossPips

                        if Candle == len(data):
                            break

                        if LowPrice[Candle] < StopLossPointBUY:

                            PipValueLoss = PipLossValue * PipValue
                            Capital = Capital - PipValueLoss

                            ResultV = Signals("LOSS", Time[i], ClosePrice[i], OpenPrice[i], TickVolume[i])

                            # Loss
                            if ResultV not in LossResultList:
                                LossResultList.append(ResultV)

                            break


                        elif ClosePrice[Candle] >= TakeProfitBUY or \
                                HighPrice[Candle] >= TakeProfitBUY:

                            PipValueWin = PipWinValue * PipValue

                            Capital = Capital + PipValueWin

                            # Win
                            ResultV = Signals("WIN", Time[i], ClosePrice[i], OpenPrice[i], TickVolume[i])
                            WinResultList.append(ResultV)

                            break


                elif BuyingOrSelling == "SELL":

                    for Candle in range(500):

                        if Candle == 0:
                            Candle = i + 1
                        else:
                            Candle = i + Candle

                        BidPrice = ClosePrice[i]
                        TakeProfitSELL = BidPrice - TakeProfitPips
                        StopLossPointSELL = BidPrice + StopLossPips

                        if Candle == len(data):
                            break

                        if HighPrice[Candle] + SpreadValue > StopLossPointSELL:

                            PipValueLoss = PipLossValue * PipValue

                            Capital = Capital - PipValueLoss

                            # Loss
                            ResultV = Signals("LOSS", Time[i], ClosePrice[i], OpenPrice[i], TickVolume[i])

                            if ResultV not in LossResultList:
                                LossResultList.append(ResultV)

                            break

                        elif ClosePrice[Candle] + SpreadValue <= TakeProfitSELL or \
                                ClosePrice[Candle] + SpreadValue <= TakeProfitSELL:

                            Pips = TakeProfitPips

                            PipValueWin = PipWinValue * PipValue
                            Capital = Capital + PipValueWin

                            # Win
                            ResultV = Signals("WIN", Time[i], ClosePrice[i], OpenPrice[i], TickVolume[i])
                            WinResultList.append(ResultV)

                            break

                else:
                    #Doji
                    ResultV = Signals("LOSS", Time[i], ClosePrice[i], OpenPrice[i], TickVolume[i])

                    if ResultV in LossResultList:
                        LossResultList.remove(ResultV)


        else:
            nothing = 'nothing'

print("End Simulation")
print("Result:")
Dojicount = int(len(SignalList) - (len(WinResultList) + len(LossResultList)))
percentageCount = str(int(len(WinResultList) / len(SignalList) * 100))
percentageCount = percentageCount + "%"
Totalwinloss = len(WinResultList) + len(LossResultList)
percentageCountReal = str(int(len(WinResultList) / Totalwinloss * 100))
percentageCountReal = percentageCountReal + "%"
print('Currency:', Currency)
print('Time Period', Timeframe)
print('Win:', len(WinResultList))
print('Loss:', len(LossResultList))
print('Doji:', Dojicount)
print('Total Signal:', len(SignalList))
print('Win ratio: ', percentageCount)
print('Win ratio (without doji): ', percentageCountReal)
print('Initial Capital: ', InitialCapital)
print('Account Balance: ', Capital)
print('Total Profit: ', Capital - InitialCapital)
