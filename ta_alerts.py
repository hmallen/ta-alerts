import configparser
import datetime
from decimal import Decimal
import logging
import numpy as np
import os
import poloniex
from pprint import pprint
import sys
import talib.abstract
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import time

config_file = 'config/config.ini'
log_file = 'logs/' + datetime.datetime.now().strftime('%m%d%Y-%H%M%S') + '.log'

loop_time = 60  # Time (seconds) between technical analysis calculations

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Add handler to output log messages to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Add handler to write log messages to file
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

if not os.path.exists('logs'):
    logger.info('Log directory not found. Creating.')
    try:
        os.makedirs('logs')
    except Exception as e:
        logger.exception('Failed to create log directory. Exiting.')
        logger.exception(e)
        sys.exit(1)
if not os.path.exists('logs/old'):
    logger.info('Log archive directory not found. Creating.')
    try:
        os.makedirs('logs/old')
    except Exception as e:
        logger.exception('Failed to create log archive directory. Exiting.')
        logger.exception(e)
        sys.exit(1)


# Get candle data
def get_candles(time_bin, product='BTC_STR'):
    valid_bins = [300, 900, 1800, 7200, 14400, 86400]

    try:
        if time_bin in valid_bins:
            data = polo.returnChartData(product, period=time_bin)
        
            candle_array = []
            for x in range(0, len(data)):
                candle = data[x]
                candle_list = []
                for k, v in candle.items():
                    candle_list.append(v)
                
                candle_array.append(candle_list)

            data_array = np.stack(np.array(candle_array, dtype=float), axis=-1)

            candle_data = {
                'date': data_array[0],
                'high': data_array[1],
                'low': data_array[2],
                'open': data_array[3],
                'close': data_array[4],
                'volume': data_array[5],
                'quoteVolume': data_array[6],
                'weightedAverage': data_array[7],
                'time_bin': time_bin
                }

            return candle_data

        else:
            logger.error('Invalid time bin given to get_candles() function. Exiting.')
            sys.exit(1)

    except Exception:
        logger.exception('Exception while retrieving candle data.')
        raise


# MACD calculation
def macd_calc(data, input_prices='close', long=26, short=10, signal=9):
    logger.debug('Calculating MACD.')
    logger.debug('Long: ' + str(long))
    logger.debug('Short: ' + str(short))
    logger.debug('Signal: ' + str(signal))
    
    try:
        macd, signal, histogram = talib.abstract.MACD(data, long, short, signal, price=input_prices)

        macd_current = macd[-1]
        signal_current = signal[-1]
        histogram_current = histogram[-1]

        macd_values = {
            'macd': macd_current,
            'signal': signal_current,
            'histogram': histogram_current,
            'time_bin': data['time_bin']
            }

        #macd_values = (macd_current, signal_current, histogram_current)

        return macd_values

    except Exception:
        logger.exception('Exception while calculating MACD.')
        raise


def telegram_message(bot, msg):
    target_user = 382606465  # @hmallen
    bot.sendMessage(chat_id=target_user, text=msg)


def example_function():
    pass


if __name__ == '__main__':
    try:
        # Read config file
        config = configparser.ConfigParser()
        config.read(config_file)
        polo_api = config['poloniex']['key']
        logger.debug('Poloniex API: ' + polo_api)
        polo_secret = config['poloniex']['secret']
        logger.debug('Poloniex Secret: ' + polo_secret)
        telegram_token = config['telegram']['token']
        logger.debug('Telegram Token: ' + telegram_token)

        # Initialize Telegram
        updater = Updater(token=telegram_token)
        #dispatcher = updater.dispatcher
        #example_handler = CommandHandler('example_command', example_function)
        #dispatcher.add_handler(example_handler)
        updater.start_polling()

        # Initialize Poloniex
        polo = poloniex.Poloniex()
        #polo = poloniex.Poloniex(polo_key, polo_secret)

        # Time bins to use for analysis
        analysis_bins = [300, 1800]

        # Alert trigger states
        alert_states = {}
        alert_states_last = {}

        # Determine initial values to set alert trigger states
        # Get candle data
        candles = []
        for val in analysis_bins:
            cand = get_candles(time_bin=val, product='BTC_STR')
            candles.append(cand)
            time.sleep(1)   # Delay to prevent excessive API calls

        # Run technical analysis
        macd_output = []
        for candle_input in candles:
            macd_values = macd_calc(candle_input, input_prices='close', long=26, short=10, signal=9)
            macd_output.append(macd_values)
            logger.debug('macd: ' + str(macd_values['macd']))
            logger.debug('signal: ' + str(macd_values['signal']))
            logger.debug('histogram: ' + str(macd_values['histogram']))

        # Display results
        for output in macd_output:
            logger.debug('Setting initial alert trigger states.')
            logger.debug('Time Bin: ' + "{:.0f}".format(output['time_bin'] / 60) + ' min')
            logger.debug('MACD: ' + str(output['macd']))
            logger.debug('Signal: ' + str(output['signal']))
            logger.debug('Histogram: ' + str(output['histogram']))

            logger.debug('Setting initial alert trigger states.')
            alert_arg = str(output['time_bin'])
            if output['histogram'] > 0:
                alert_states[alert_arg] = ['OVER', 'na']
            else:
                alert_states[alert_arg] = ['UNDER', 'na']

            if output['macd'] > 0:
                alert_states[alert_arg][1] = 'ABOVE'
            else:
                alert_states[alert_arg][1] = 'BELOW'
            logger.debug('Alert State (' + alert_arg + '): ' + str(alert_states[alert_arg]))
            alert_states_last[alert_arg] = alert_states[alert_arg]
    
    except Exception as e:
        logger.exception('Failed during initialization. Exiting.')
        logger.exception(e)
        sys.exit(1)

    loop_count = 0
    while (True):
        loop_count += 1
        print()
        logger.debug('loop_count: ' + str(loop_count))
        try:
            # Get candle data
            candles = []
            for val in analysis_bins:
                cand = get_candles(time_bin=val, product='BTC_STR')
                candles.append(cand)
                time.sleep(1)   # Delay to prevent excessive API calls

            # Run technical analysis
            macd_output = []
            for candle_input in candles:
                macd_values = macd_calc(candle_input, input_prices='close', long=26, short=10, signal=9)
                macd_output.append(macd_values)
                #logger.debug('macd: ' + str(macd_values['macd']))
                #logger.debug('signal: ' + str(macd_values['signal']))
                #logger.debug('histogram: ' + str(macd_values['histogram']))

            # Display results
            for output in macd_output:
                print()
                logger.info('Time Bin: ' + "{:.0f}".format(output['time_bin'] / 60) + ' min')
                logger.info('MACD: ' + str(output['macd']))
                logger.info('Signal: ' + str(output['signal']))
                logger.info('Histogram: ' + str(output['histogram']))

                alert_arg = str(output['time_bin'])
                if output['histogram'] > 0:
                    alert_states[alert_arg][0] = 'OVER'
                else:
                    alert_states[alert_arg][0] = 'UNDER'

                if output['macd'] > 0:
                    alert_states[alert_arg][1] = 'ABOVE'
                else:
                    alert_states[alert_arg][1] = 'BELOW'
                logger.debug('Alert State (' + alert_arg + '): ' + str(alert_states[alert_arg]))

            # Check for changes
            for key in alert_states:
                if alert_states[key][0] != alert_states_last[key][0]:
                    print()
                    logger.debug('MACD-Signal crossover detected. Sending Telegram alert.')
                    telegram_message = "{:.0f}".format(output['time_bin'] / 60) + ' min ' + ' MACD crossed ' + alert_states[key][0] + ' signal.'
                    telegram_message(updater.bot, telegram_message)
                    alert_states_last[key][0] = alert_states[key][0]
                if alert_states[key][1] != alert_states_last[key][1]:
                    print()
                    logger.debug('MACD-Zero crossover detected. Sending Telegram alert.')
                    telegram_message = "{:.0f}".format(output['time_bin'] / 60) + ' min ' + ' MACD crossed ' + alert_states[key][1] + ' zero.'
                    telegram_message(updater.bot, telegram_message)
                    alert_states_last[key][1] = alert_states[key][1]

            time.sleep(loop_time)

        except Exception as e:
            logger.exception('Exception raised.')
            logger.exception(e)

        except KeyboardInterrupt:
            updater.stop()
            sys.exit()
