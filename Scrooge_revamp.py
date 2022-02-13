# "Standard libraries only..."
# from asyncore import read
import calendar
# from distutils.command.clean import clean

import json
# from tracemalloc import start
# from typing import Iterator
import urllib.request as request
from datetime import datetime


# To give us some colors to play with...
class Color:
    CYAN = '\033[1;36;48m'
    BLUE = '\033[1;34;48m'
    GREEN = '\033[1;32;48m'
    RED = '\033[1;31;48m'
    END = '\033[1;37;0m'


DATE_FORMAT_ERROR = ("Something went wrong with the format OR day/month value"
                     "is not realistic. \n")
DATE_FUTURE_ERROR = ("Scrooge McClairvoyant, is that you? Please enter a date"
                     "that is not from the future.\n")
DATE_PAST_ERROR = "Bitcoin wasn't invented quite yet back then...\n"

DATE_ORDER_ERROR = ("Scrooge's ability to bend space-time continuum is"
                    "currently under maintenance.\nPlease make sure end"
                    " date is actually later than start date.\n")


def date_sanity_check(date=datetime, comparator_date=datetime.min):
    if date > datetime.today():
        print(DATE_FUTURE_ERROR)
        return False

    if date.year < 2008:
        print(DATE_PAST_ERROR)
        return False

    if date < comparator_date and \
       comparator_date != datetime.min:
        print(DATE_ORDER_ERROR)
        return False

    return True


def read_a_date(start_or_end="", comparator_date=datetime.min):
    # comparator date helps when asking for the END date, where END needs to be
    # after START...
    date_time_stamp = datetime
    while True:
        print(f"Please enter the {start_or_end} date as DD.MM.YYYY")
        try:
            date = input(">> ")
            date_datetime = datetime.strptime(date, "%d.%m.%Y")

            if not date_sanity_check(date_datetime, comparator_date):
                continue

        except ValueError:
            print(DATE_FORMAT_ERROR)

        else:
            date_time_stamp = calendar.timegm(date_datetime.timetuple())
            print(f"{start_or_end} date entered succesfully! \n")
            break

    return date_time_stamp, date_datetime


def read_both_dates():
    start_date_stamp, start_datetime = read_a_date("START")
    end_date_stamp, end_datetime = read_a_date("END", start_datetime)

    start_date_human = \
        datetime.utcfromtimestamp(start_date_stamp).strftime('%d.%m.%Y')
    end_date_human = \
        datetime.utcfromtimestamp(end_date_stamp).strftime('%d.%m.%Y')

    return start_date_stamp, end_date_stamp, start_date_human, end_date_human


def fetch_data(start_date, end_date):
    # should add an hour to the end to ensure also
    # getting the last desired date...
    magic_number = 3600
    url = 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range?'\
        + 'vs_currency=eur&from=' + str(start_date) + \
          '&to=' + str(end_date + magic_number)

    print("Fetching data from ", url, "\n")
    file = request.urlopen(url)
    data_to_clean = json.loads(file.read().decode('utf-8'))

    return data_to_clean


def clean_data(raw_data):

    cleaned_data = {}
    for key in raw_data:
        cleaned_data[key] = []

    for date in raw_data['prices']:
        # convert to human-readable form
        current = \
            datetime.utcfromtimestamp(date[0] / 1000).strftime('%d.%m.%Y')

        if len(cleaned_data['prices']) == 0 or \
           current != cleaned_data['prices'][-1][0]:
            for key in cleaned_data:
                cleaned_data[key].append([current, date[1]])

    return cleaned_data


def longest_bearish_streak(price_data):

    bear_longest = []
    bear_temp = []

    iterator = iter(price_data)
    prev = next(iterator)

    for current in iterator:
        if current[1] < prev[1]:  # current[date, price]
            bear_temp.append(current)

            if len(bear_temp) > len(bear_longest):
                bear_longest = bear_temp.copy()

            prev = current
            continue

        prev = current
        bear_temp.clear()

    return bear_longest


def trading_volume(all_data):
    highest_vol = 0
    price_at_highest_vol = 0
    highest_date = 0

    for index, current in enumerate(all_data['total_volumes']):
        if current[1] > highest_vol:
            highest_vol = float(current[1])  # current[date, total_volume]
            highest_date = current[0]
            price_at_highest_vol = float(all_data['prices'][index][1])

    return highest_vol, price_at_highest_vol, highest_date


def time_machine(price_data):

    low_value = price_data[0][1]
    low_date = price_data[0][0]
    initial_date = price_data[0][0]
    high_value = 0
    high_date = datetime
    profit = 0

    for idx, current in enumerate(price_data):        
        temp_low_value = current[1]
        temp_low_date = current[0]

        print("current :", temp_low_value)
        if temp_low_value < low_value or temp_low_date == initial_date:
            temp_high = max(price_data[idx:], key=lambda x: x[1])
            temp_high_value = temp_high[1]
            temp_high_date = temp_high[0]
            temp_profit = temp_high_value / temp_low_value

            if temp_profit > profit:
                profit = temp_profit
                low_value = temp_low_value
                low_date = temp_low_date
                high_value = temp_high_value
                high_date = temp_high_date

    return profit, low_value, low_date, high_value, high_date


# MAIN PROGRAM BEGINS
if __name__ == '__main__':
    print("\n\n\n\n")
    start_date, end_date, start_human, end_human = read_both_dates()
    data_to_clean = fetch_data(start_date, end_date)
    final_data = clean_data(data_to_clean)

    commands = {1: 'Enter new date range',
                2: 'Find longest bearish trend',
                3: 'Find highest trading volume',
                4: 'Find biggest profit',
                5: 'Quit'}

    # Keep printing out available commands and asking for a new command until
    # Quit (corresponding number...) is given.
    while True:
        print(f"{Color.RED}AVAILABLE COMMANDS{Color.END}")
        for command in commands:
            print(command, ". ", commands[command], sep="")
        cmd = input("Please choose a number and press ENTER\n>> ")

        # Read data
        if cmd == str(1):
            start_date, end_date, start_human, end_human = read_both_dates()
            data_to_clean = fetch_data(start_date, end_date)
            final_data = clean_data(data_to_clean)

        # Find longest bearish streak
        elif cmd == str(2):
            if len(final_data['prices']) < 2:
                print("Can't search for trends with fewer than 2 samples!\n")
                continue

            longest_bear = longest_bearish_streak(final_data['prices'])
            if not longest_bear:
                print("No bearish shenanigans happening in this range "
                      "of dates!\n")
                continue

            bear_start_date = longest_bear[0][0]  # list[date, price]
            bear_end_date = longest_bear[-1][0]
            print(f"According to the data from CoinGecko, between "
                  f"{Color.CYAN}{start_human} and {end_human}{Color.END}"
                  f" the longest downward trend for Bitcoin lasted for "
                  f"{Color.RED}{len(longest_bear)}{Color.END} days. \n"
                  f"This particular bear roared between "
                  f"{Color.CYAN}{bear_start_date} and "
                  f"{bear_end_date}{Color.END}.\n")

        # Find highest trading volume and its monetary value
        elif cmd == str(3):
            highest_vol, price_at_highest_vol, highest_date = \
                trading_volume(final_data)

            print(f"According to the data from CoinGecko, highest trading "
                  f"volume occurred on {Color.CYAN}{highest_date}"
                  f"{Color.END} with a trading volume of "
                  f"{Color.CYAN}{highest_vol:,.2f}{Color.END} units. \n"
                  f"BTC value was {Color.GREEN}{price_at_highest_vol:,.2f}"
                  f"{Color.END} eur, so total trade value was {Color.GREEN}"
                  f"{highest_vol * price_at_highest_vol:,}{Color.END} eur.\n")
        
        # Find the most profitable date combination to invest and sell
        elif cmd == str(4):
            profit, low_value, low_date, high_value, high_date = \
                time_machine(final_data['prices'])

            if high_value < low_value:
                print(f"Sorry Scrooge, but no profit to be made in this date"
                      f"range!\n")

            print(f"Your investment would have been "
                  f"{Color.GREEN}{profit * 100:.2f}%{Color.END} of its initial"
                  f" value,\nif you just had bought BTC on {Color.CYAN}"
                  f"{low_date}{Color.END}, when value was {Color.RED}"
                  f"{low_value:,.2f} {Color.END}eur \nand sold on "
                  f"{Color.CYAN}{high_date}{Color.END} when value"
                  f" was {Color.GREEN}{high_value:,.2f}{Color.END}eur\n")

        elif cmd == str(5):
            print("Goodbye, you absolute legend!")
            break

        else:
            print(f"Something went wrong. Did you give a number and the number"
                  f"only?\n")
