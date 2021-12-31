# Mikael U.
# Small program to help Scrooge McDuck to speculate how much money he has lost by not jumping on the
# crypto train


# "Standard libraries only..."
import calendar
import json
import urllib.request as request
from datetime import datetime, date, time, timezone


# To give us some colors to play with...
class Color:
    CYAN = '\033[1;36;48m'
    BLUE = '\033[1;34;48m'
    GREEN = '\033[1;32;48m'
    RED = '\033[1;31;48m'
    END = '\033[1;37;0m'


def read_dates():
    """This function will be called to ask user-entered dates and form epoch/unix timestamps
        returns timestamps for start and end date"""

    error_message = "Something went wrong with the format OR day/month value is not realistic. \n"
    stamp_start = datetime
    # Keep asking for a START date until one is provided in proper format dd.mm.yyyy or d.m.yyyy
    # convert to epoch/unix timestamp when proper format is entered
    while True:
        print("Please enter the START date as DD.MM.YYYY")
        try:
            start_date = input(">> ")
            start_dt = datetime.strptime(start_date, "%d.%m.%Y")
            if start_dt > datetime.today():
                print("Scrooge McClairvoyant, is that you? Please enter a date that is not from the future.\n")
                continue
            if start_dt.year < 2008:
                print("Bitcoin wasn't invented quite yet back then...\n")
                continue
        except ValueError:
            print(error_message)
        else:
            stamp_start = calendar.timegm(start_dt.timetuple())
            print("Starting date entered successfully! \n")
            break

    # Keep asking for an END date until one is provided in proper format dd.mm.yyyy or d.m.yyyy
    # convert to epoch/unix timestamp when proper format is entered
    while True:
        print("Please enter the END date as DD.MM.YYYY")
        try:
            end_date = input(">> ")
            end_dt = datetime.strptime(end_date, "%d.%m.%Y")
            # if a date is found in acceptable format, we need to make sure it actually is later than our starting
            # date...
            if end_dt:
                stamp_end = calendar.timegm(end_dt.timetuple())
                if stamp_end < stamp_start:
                    print("Scrooge's ability to bend space-time continuum is currently under maintenance. \n"
                          "Please make sure end date is actually later than start date.\n")
                    continue
        except ValueError:
            print("Something went wrong with the format.")
        else:
            stamp_end = calendar.timegm(end_dt.timetuple())
            print("Ending date entered successfully!\n")
            break

    return stamp_start, stamp_end


def get_data(start, end):
    """
    :param start: starting date in epoch/unix timestamp
    :param end: ending date in epoch/unix timestamp
    :return: data with values for price, volume and market_cap only from 00:00 UTC or as close to is as possible
    """
    # "Tip: You should add 1 hour to the `to` input to make sure
    # that you always get data for the end date as well." -> add magic_number to end date timestamp
    magic_number = 3600
    url = 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range?vs_currency=eur&from=' + str(start) + \
          '&to=' + str(end + magic_number)

    print("Fetching data from ", url, "\n")
    file = request.urlopen(url)
    data_to_clean = json.loads(file.read().decode('utf-8'))

    # We want to only keep the values from 00:00 UTC or as close to it as possible...so
    # first we replace all timestamps in datamatrix with actual human-readable dates
    # For example data_to_clean['prices'] contains tuples [timestamp, price]. So data_to_clean['prices'][-1][0]
    # would give the timestamp of last entry in data_to_clean['prices']
    for i in range(len(data_to_clean['prices'])):
        key = datetime.utcfromtimestamp(data_to_clean['prices'][i][0] / 1000).strftime('%d.%m.%Y')
        data_to_clean['prices'][i][0] = key
        data_to_clean['total_volumes'][i][0] = key
        data_to_clean['market_caps'][i][0] = key

    cleaned_data = {"prices": [data_to_clean['prices'][0]],
                    "total_volumes": [data_to_clean['total_volumes'][0]],
                    "market_caps": [data_to_clean['market_caps'][0]]}

    # Now we can compare the human-readable dates between N and N-1...and if the date already exists in cleaned_date,
    # we move on. Data_to_clean is sorted by time. Hence, we can trust that if we already picked the first value
    # for certain date to be entered into cleaned_data, it actually is the first datapoint of given day thus closest
    # to 00:00 UTC and no further dataentries for the same day need to be considered.
    for i in range(len(data_to_clean['prices'])):
        if data_to_clean['prices'][i][0] != cleaned_data['prices'][-1][0]:
            cleaned_data['prices'].append(data_to_clean['prices'][i])
            cleaned_data['total_volumes'].append(data_to_clean['total_volumes'][i])
            cleaned_data['market_caps'].append(data_to_clean['market_caps'][i])

    return cleaned_data


def bear_streak(price_data):
    """
    :param price_data: this is just cleaned_data['prices'], containing [date, BTC value]
    :return: return None is called to break out from function if criteria for data is not met. Else just print out the
             streak info.

    Try to find the longest bearish streak aka. downward trend for BTC value from given data.
    If N + 1 < N, (N + 1) makes it to  our list.
    """

    if len(price_data) < 2:
        print("Can't search for trends with fewer than 2 samples!")
        return None

    bear_longest = []
    bear_temp = []
    # Go through the data and keep appending bear_temp while the BTC values are decreasing.
    # If trend is broken, compare bear_temp to our current bear_longest and start looking for a new trend.
    for i in range(len(price_data)):
        if i >= 1 and price_data[i-1][1] >= price_data[i][1]:
            bear_temp.append(price_data[i])
            if len(bear_temp) > len(bear_longest):
                bear_longest = bear_temp.copy()
        else:
            bear_temp.clear()

    if not bear_longest:
        print("No bearish shenanigans happening in this range of dates!")
        return None

    start_date = price_data[0][0]
    end_date = price_data[-1][0]
    bear_start_date = bear_longest[0][0]
    bear_end_date = bear_longest[-1][0]
    print(f"According to the data from CoinGecko, between {Color.CYAN}{start_date} and {end_date}{Color.END} "
          f"the longest downward trend for Bitcoin lasted for {Color.RED}{len(bear_longest)}{Color.END} days. \n"
          f"This particular bear roared between {Color.CYAN}{bear_start_date} and {bear_end_date}{Color.END}.\n")


def trading_volume(all_data):
    """
    :param all_data: as the name implies
    Find and print out information related to the highest trading volume in given date range.
    """
    highest_vol = 0
    price_at_hvol = 0
    highest_date = 0

    for i in range(len(all_data['total_volumes'])):
        if int(all_data['total_volumes'][i][1]) > highest_vol:
            highest_vol = float(all_data['total_volumes'][i][1])
            price_at_hvol = float(all_data['prices'][i][1])
            highest_date = all_data['total_volumes'][i][0]

    print(f"According to the data from CoinGecko, highest trading volume occurred on {Color.CYAN}{highest_date}"
          f"{Color.END} with a trading volume of {Color.CYAN}{highest_vol:,.2f}{Color.END} units. \nBTC value was "
          f"{Color.GREEN}{price_at_hvol:,.2f}{Color.END} eur, so total trade value was "
          f"{Color.GREEN}{highest_vol * price_at_hvol:,}{Color.END} eur.\n")


def time_machine(price_data):
    """
    :param price_data: is equal to clean_data['prices'] containing [date, BTC value]
    :return: None, if it is not possible to make profit within this date range

    Find the lowest and highest BTC values. Or more accurately, the highest possible factor highvalue / lowvalue so that
    low value occurs before high value"""
    low_value = price_data[0][1]
    low_date = price_data[0][0]
    high_value = 0
    high_date = datetime
    profit = 0

    # This is a bit ugly with 2 nested for-loops, but should get the job done. First, iterate from "left to right"
    # trying to find a smaller value than the previous smallest value. When you find a smaller value, start looking
    # for bigger-than-previous-biggest values from the remainder of the list. If a bigger value is found,
    # calculate factor(aka profit) by division. If this factor > previous biggest profit, store the
    # high and low coin values with their corresponding dates.
    for i in range(len(price_data)):
        temp_low = price_data[i][1]
        if temp_low <= low_value:
            # A new lowest value was found, let's find the high value providing the biggest possible factor...
            temp_highest = 0
            for j in range(i+1, len(price_data)):
                temp_high = price_data[j][1]
                if temp_high > temp_highest:
                    temp_highest = temp_high
                    factor = temp_highest / temp_low
                    if factor > profit:
                        profit = factor
                        high_value = temp_highest
                        low_value = temp_low
                        low_date = price_data[i][0]
                        high_date = price_data[j][0]

    # High value needs to be after low value in order to make profit
    if high_value < low_value:
        print(f"Sorry Scrooge, but no profit to be made in this date range!\n")
        return None

    print(f"Your investment would have been {Color.GREEN}{profit * 100:.2f}%{Color.END} of its initial value,"
          f"\nif you just had bought BTC on {Color.CYAN}{low_date}{Color.END}, when value was "
          f"{Color.RED}{low_value:,.2f} {Color.END}eur \nand sold on {Color.CYAN}{high_date}{Color.END} when value"
          f"was {Color.GREEN}{high_value:,.2f}{Color.END}eur\n")


if __name__ == '__main__':

    print(f"This is a small script purely intended for those wishing to torture themselves by asking \"what if I had "
          f"spent 500 euros on BTC back in 2015 or so...?\"")

    # Ask for initial date range and form data
    date_start, date_end = read_dates()
    data = get_data(date_start, date_end)

    commands = {1: 'Enter new date range',
                2: 'Find longest bearish trend',
                3: 'Find highest trading volume',
                4: 'Find biggest profit',
                5: 'Quit'}

    # Keep printing out available commands and asking for a new command until Quit (command 5 atm) is given.
    while True:

        for command in commands:
            print(command, ". ", commands[command], sep="")
        cmd = input("Please choose a number and press ENTER\n>> ")

        if cmd == str(1):
            date_start, date_end = read_dates()
            data = get_data(date_start, date_end)

        elif cmd == str(2):
            bear_streak(data['prices'])

        elif cmd == str(3):
            trading_volume(data)

        elif cmd == str(4):
            time_machine(data['prices'])

        elif cmd == str(5):
            print("Goodbye, you absolute legend!")
            break

        else:
            print("Something went wrong. Did you give a number and the number only?")











