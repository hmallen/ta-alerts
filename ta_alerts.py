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

# User modifiable parameters
analysis_bins = [300, 1800] # Desired candles sizes for analysis
telegram_user = 382606465  # @hmallen
loop_time = 30

# Required constants
valid_bins = [300, 900, 1800, 7200, 14400, 86400]   # Valid candle sizes for API

config_file = 'config/config.ini'
log_file = 'logs/' + datetime.datetime.now().strftime('%m%d%Y-%H%M%S') + '.log'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Add handler to output log messages to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

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

# Add handler to write log messages to file
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# Get candle data
def get_candles(product, time_bin):
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
            'histogram': histogram_current
            }

        return macd_values

    except Exception:
        logger.exception('Exception while calculating MACD.')
        raise


def telegram_message(msg):
    try:
        updater.bot.sendMessage(chat_id=telegram_user, text=msg)

    except Exception:
        logger.exception('Exception while sending Telegram alert.')
        raise


if __name__ == '__main__':
    try:
        # Read config file
        config = configparser.ConfigParser()
        config.read(config_file)

        #polo_api = config['poloniex']['key']
        #logger.debug('Poloniex API: ' + polo_api)
        #polo_secret = config['poloniex']['secret']
        #logger.debug('Poloniex Secret: ' + polo_secret)

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

        # State of indicator lines (ie. Crossed-over/under, Above/below zero)
        indicator_states = {}
        indicator_states_last = {}
        for val in analysis_bins:
            indicator_states[val] = {}
            indicator_states[val]['cross_state'] = None
            indicator_states[val]['zero_state'] = None
            indicator_states_last[val] = {}
            indicator_states_last[val]['cross_state'] = None
            indicator_states_last[val]['zero_state'] = None

    except Exception as e:
        logger.exception('Failed during initialization. Exiting.')
        logger.exception(e)
        sys.exit(1)

    loop_count = 0
    while (True):
        loop_count += 1
        logger.debug('loop_count: ' + str(loop_count))
        try:
            results = {}
            for test in analysis_bins:
                candles = get_candles(product='BTC_STR', time_bin=test)
                results[test] = macd_calc(data=candles)

                print()
                logger.info('Time Bin: ' + "{:.0f}".format(test / 60) + ' min')
                logger.info('MACD: ' + str(results[test]['macd']))
                logger.info('Signal: ' + str(results[test]['signal']))
                logger.info('Histogram: ' + str(results[test]['histogram']))
                print()
                
                time.sleep(1)

            for key in results:
                if results[key]['histogram'] > 0:
                    indicator_states[key]['cross_state'] = 'ABOVE'
                else:
                    indicator_states[key]['cross_state'] = 'BELOW'

                if results[key]['macd'] > 0:
                    indicator_states[key]['zero_state'] = 'ABOVE'
                else:
                    indicator_states[key]['zero_state'] = 'BELOW'

                logger.debug('indicator_states[' + str(key) + '][\'cross_state\']: ' + indicator_states[key]['cross_state'])
                logger.debug('indicator_states[' + str(key) + '][\'zero_state\']: ' + indicator_states[key]['zero_state'])
                print()
            
            alert_list = []
            for key in indicator_states:
                if indicator_states[key]['cross_state'] != indicator_states_last[key]['cross_state']:
                    alert_message = "{:.0f}".format(key / 60) + ' min ' + 'MACD-Signal crossed ' + indicator_states[key]['cross_state'] + '.'
                    logger.debug('Appending alert_message: ' + alert_message)
                    #telegram_message(alert_message)
                    alert_list.append(alert_message)
                    indicator_states_last[key]['cross_state'] = indicator_states[key]['cross_state']
                else:
                    logger.debug('No MACD-Signal change.')

                if indicator_states[key]['zero_state'] != indicator_states_last[key]['zero_state']:
                    alert_message = "{:.0f}".format(key / 60) + ' min ' + 'MACD-Zero crossed ' + indicator_states[key]['zero_state'] + '.'
                    logger.debug('Appending alert_message: ' + alert_message)
                    #telegram_message(alert_message)
                    alert_list.append(alert_message)
                    indicator_states_last[key]['zero_state'] = indicator_states[key]['zero_state']
                else:
                    logger.debug('No MACD-Zero change.')

            if loop_count > 1 and len(alert_list) > 0:
                logger.info('Alert list not empty. Sending via Telegram.')
                for alert in alert_list:
                    logger.debug('Sending Telegram alert: ' + alert)
                    telegram_message(alert)
                    time.sleep(1)
            
            time.sleep(loop_time)

        except Exception as e:
            logger.exception('Exception raised.')
            logger.exception(e)

        except KeyboardInterrupt:
            updater.stop()
            sys.exit()
