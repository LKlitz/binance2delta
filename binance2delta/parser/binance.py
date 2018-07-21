# -*- coding: utf-8 -*-

# Copyright (c) 2016-2017 by Lars Klitzke, Lars.Klitzke@gmail.com
# All Rights Reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
#    * Names of its contributors may be used to endorse or promote
#      products derived from this software without specific prior
#      written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# REGENTS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
import datetime

from transaction import CryptoList, Position, Fee, CryptoTransaction

from binance2delta.parser.parser import TradeHistoryParser, ParserOutdatedError


def _market_to_trading_pair(market):
    """
    This function will convert the market column of the binance file into a trading pair

    Args:
        market: A value of the market column of the csv file

    Returns:
        A tuple with two entries representing the trading pair or None if the pair is unknown

    """

    # at first, get a list of all available cryptocoins
    coins = CryptoList()

    def __get_currencies(other_symbol, symbol):
        if market.startswith(symbol):
            # start of the string
            return c, coins.find_symbol(other_symbol)
        elif market.endswith(symbol):
            # end of the string
            return coins.find_symbol(other_symbol), c

    # now check if any of the coins symbol name is in the market
    for c in coins:
        second_symbol = market.replace(c.symbol, "")

        if coins.find_symbol(second_symbol):
            # market is valid
            return __get_currencies(second_symbol, c.symbol)


class BinanceParser(TradeHistoryParser):
    """
    Parses csv files of the Binance exchange platform.

    """

    _COLUMN_DATE = "Date(UTC)"

    _COLUMN_TYPE = "Type"

    _COLUMN_MARKET = "Market"

    _COLUMN_PRICE = "Price"

    _COLUMN_FEE_COIN = "Fee Coin"

    _ORDER_SELL = "Sell"

    _ORDER_BUY = "Buy"

    _COLUMN_TOTAL = "Total"

    _COLUMN_FEE = "Fee"

    _COLUMN_COIN_AMOUNT = "Amount"

    _COLUMNS = [
        _COLUMN_DATE,
        _COLUMN_MARKET,
        _COLUMN_TYPE,
        _COLUMN_PRICE,
        _COLUMN_COIN_AMOUNT,
        _COLUMN_TOTAL,
        _COLUMN_FEE,
        _COLUMN_FEE_COIN
    ]

    def parse(self, csv_file):

        csv_content = self._read_file(csv_file)

        # the first line is the header of the csv columns
        header = csv_content[0]
        del csv_content[0]

        # check if each entry in the header is in our list
        for c in header:
            if c not in BinanceParser._COLUMNS:
                # otherwise, rise an exception that the parser is out of date
                raise ParserOutdatedError('The column {} is unknown. The parser has to be updated!'.format(c))

        transactions = []

        # parse all other rows
        for row in csv_content:
            row_ = TradeHistoryParser.Row(row=row, header=header)

            base, quota = _market_to_trading_pair(row_[self._COLUMN_MARKET])

            # old binance files had different way to store datetimes which will not be converted
            # by the xlsx module by default. Thus, we have to check this manually.
            if not isinstance(row_.get(self._COLUMN_DATE), datetime.datetime):
                row_[self._COLUMN_DATE] = datetime.datetime.strptime(row_[self._COLUMN_DATE], "%d.%m.%y %H:%M")

            # convert the row to a transaction
            transactions.append(CryptoTransaction(
                datetime=row_[self._COLUMN_DATE],
                trading_pair=(Position(amount=row_[self._COLUMN_TOTAL], currency=quota),
                              Position(amount=row_[self._COLUMN_COIN_AMOUNT], currency=base)),
                trading_type=row_[self._COLUMN_TYPE],
                price=row_[self._COLUMN_PRICE],
                fee=Fee(row_[self._COLUMN_FEE], row_[self._COLUMN_FEE_COIN]),
                exchange="Binance"
            ))

        return transactions

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class BinanceCrawlerParser(TradeHistoryParser):
    """
    Parses csv files created by the binanceCrawler.

    """

    _COLUMN_TIME = 'time'
    _COLUMN_SIDE = 'side'
    _COLUMN_TRADEID = 'tradeId'
    _COLUMN_QUANTITY = 'qty'
    _COLUMN_FEE_COIN = 'feeAsset'
    _COLUMN_SYMBOL = 'symbol'
    _COLUMN_TOTAL_QUOTA = 'totalQuota'
    _COLUMN_REALPnl = 'realPnl'
    _COLUMN_QUOTE_ASSET = 'quoteAsset'
    _COLUMN_BASE_ASSET = 'baseAsset'
    _COLUMN_ID = 'id'
    _COLUMN_FEE = 'fee'
    _COLUMN_PRICE = 'price'
    _COLUMN_ACTIVE_BUY = 'activeBuy'

    _COLUMNS = [
        _COLUMN_TIME,
        _COLUMN_SIDE,
        _COLUMN_TRADEID,
        _COLUMN_QUANTITY,
        _COLUMN_FEE_COIN,
        _COLUMN_SYMBOL,
        _COLUMN_TOTAL_QUOTA,
        _COLUMN_REALPnl,
        _COLUMN_QUOTE_ASSET,
        _COLUMN_BASE_ASSET,
        _COLUMN_ID,
        _COLUMN_FEE,
        _COLUMN_PRICE,
        _COLUMN_ACTIVE_BUY,
    ]

    def parse(self, csv_file):

        csv_content = self._read_file(csv_file)

        # the first line is the header of the csv columns
        header = csv_content[0]
        del csv_content[0]

        # check if each entry in the header is in our list
        for c in header:
            if c not in BinanceCrawlerParser._COLUMNS:
                # otherwise, rise an exception that the parser is out of date
                raise ParserOutdatedError('The column {} is unknown. The parser has to be updated!'.format(c))

        transactions = []

        # parse all other rows
        for row in csv_content:
            row_ = TradeHistoryParser.Row(row=row, header=header)

            base, quota = _market_to_trading_pair(row_[self._COLUMN_SYMBOL])

            transactions.append(CryptoTransaction(
                datetime=datetime.datetime.utcfromtimestamp(row_[self._COLUMN_TIME] / 1000),
                trading_pair=(Position(amount=row_[self._COLUMN_TOTAL_QUOTA], currency=quota),
                              Position(amount=row_[self._COLUMN_QUANTITY], currency=base)),
                trading_type=row_[self._COLUMN_SIDE],
                price=row_[self._COLUMN_PRICE],
                fee=Fee(row_[self._COLUMN_FEE], row_[self._COLUMN_FEE_COIN]),
                exchange="Binance"
            ))

        return transactions

    def __init__(self, **kwargs):

        super().__init__(**kwargs)