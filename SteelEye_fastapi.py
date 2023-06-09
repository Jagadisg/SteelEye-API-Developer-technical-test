from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Query
import json
from pydantic import BaseModel, Field
import uvicorn
app = FastAPI()


class TradeDetails(BaseModel):
    buySellIndicator: str = Field(description="A value of BUY for buys, SELL for sells.")
    price: float | int = Field(description="The price of the Trade.")
    quantity: int = Field(description="The amount of units traded.")


class Trade(BaseModel):
    asset_class: Optional[str] = Field(alias="assetClass", default=None,
                                     description="The asset class of the instrument traded. E.g. Bond, Equity, FX...etc")
    counterparty: Optional[str] = Field(default=None, description="The counterparty the trade was executed with. May not always be available")
    instrumentId: str = Field(alias="instrumentId", description="The ISIN/ID of the instrument traded. E.g. TSLA, AAPL, AMZN...etc")
    instrumentName: str = Field(alias="instrumentName", description="The name of the instrument traded.")
    tradeDateTime: Optional[datetime] = Field(description="The date-time the Trade was executed")
    tradeDetails: TradeDetails = Field(description="The details of the trade, i.e. price, quantity")
    tradeId: Optional[int] = Field(alias="tradeId", default=None, description="The unique ID of the trade")
    trader: str = Field(description="The name of the Trader")

with open("SteelEye_fastapi.json", 'r') as f:
    trade = json.load(f)
    print(trade)

@app.post("/addtrade",status_code=200)
def add_trade(trade1:Trade):
    tradeId = max([t['tradeId'] for t in trade['trade']]) + 1
    new_trade = {
            "assetClass":trade1.assetClass,
            "counterparty":trade1.counterparty,
            "instrumentId":trade1.instrumentId,
            "instrumentName":trade1.instrumentName,
            "tradeDateTime":trade1.tradeDateTime.strftime("%Y-%m-%dT%H:%M:%SZ") if trade1.tradeDateTime else None,
            "tradeDetails":{
                "buySellIndicator":trade1.tradeDetails.buySellIndicator,
                "price":trade1.tradeDetails.price,
                "quantity":trade1.tradeDetails.quantity
            },
            "tradeId":tradeId,
            "trader": trade1.trader
        }
    trade["trade"].append(new_trade)
     
    with open("SteelEye_fastapi.json",'w') as f:
        json.dump(trade,f)
    return new_trade


@app.get("/listtrade/{tradeId}")
def single_trade(tradeId : int):
    single_trade = [t for t in trade["trade"] if t['tradeId'] == tradeId]
    return single_trade[0] if len(single_trade) > 0 else {}

@app.get("/trades",status_code=200)
def search(search : str):
    trades = [srch_trade for srch_trade in trade["trade"] if search.lower() in srch_trade["counterparty"].lower() or search.lower() in srch_trade["instrumentId"].lower() or search.lower() in srch_trade["instrumentName"].lower() or search.lower() in srch_trade["trader"].lower()]
    return trades

@app.post("/filtertrades",status_code=200)
def advanced_filter(
    assetClass: Optional[str] = None,
    end: Optional[str] = None,
    maxPrice: Optional[float | int] = None,
    minPrice: Optional[float | int] = None,
    start: Optional[str] = None,
    tradeType: Optional[str] = None
):
    filtered_trades = trade["trade"]
    print(filtered_trades[0]["asset_class"])
    if assetClass:
        filtered_trades = [trade for trade in filtered_trades if trade["asset_class"].lower() == assetClass.lower()]
    if end:
        filtered_trades = [trade for trade in filtered_trades if trade["tradeDateTime"] <= end]
    if maxPrice:
        filtered_trades = [trade for trade in filtered_trades if trade["tradeDetails"]["price"] <= maxPrice]
    if minPrice:
        filtered_trades = [trade for trade in filtered_trades if trade["tradeDetails"]["price"] >= minPrice]
    if start:
        filtered_trades = [trade for trade in filtered_trades if trade["tradeDateTime"] >= start]
    if tradeType:
        filtered_trades = [trade for trade in filtered_trades if trade["tradeDetails"]["buySellIndicator"].lower() == tradeType.lower()]
    return filtered_trades

@app.get("/listtrade",status_code=200)
def list_trade(assetClass: Optional[str] = None,
    end: Optional[datetime] = None,
    maxPrice: Optional[float] = None,
    minPrice: Optional[float] = None,
    start: Optional[datetime] = None,
    tradeType: Optional[str] = None,
    page: Optional[int] = Query(1, gt=0, description="Page number for pagination"),
    limit: Optional[int] = Query(10, gt=0, description="Number of trades per page"),
    sort: Optional[str] = Query(None, description="Sort trades by a field"),
    order: str = Query("asc", regex="^(asc|desc)$", description="Sorting order")
):
    filtertrades = advanced_filter(assetClass, end, maxPrice, minPrice, start, tradeType)
    total_trades = len(filtertrades)
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_trades = filtertrades[start_index:end_index]
    if sort:
        paginated_trades = sorted(paginated_trades, key=lambda t: getattr(t, sort))
    if order == "desc":
        paginated_trades = list(reversed(paginated_trades))

    return paginated_trades

uvicorn.run(app,host="127.0.0.1", port=8000)