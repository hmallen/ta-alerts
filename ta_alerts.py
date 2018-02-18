import argparse
import configparser
import datetime
from decimal import Decimal
import json
import logging
import numpy as np
import os
import poloniex
from pprint import pprint
import sys
import talib.abstract
#from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, Updater, Filters
import time

# User-modifiable variables
loop_time = 30

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', default=False, help='Debug mode.')
parser.add_argument('-p', '--pepe', action='store_true', default=False, help='Pepe greeting on user connection.')
args = parser.parse_args()

debug_mode = args.debug
pepe_greeting = args.pepe

# System variables
log_file = 'logs/' + datetime.datetime.now().strftime('%m%d%Y-%H%M%S') + '.log'
telegram_config_file = 'config/config.ini'
telegram_user_file = 'telegram_users.txt'
telegram_pepe_file = 'resources/matrix_pepe.gif'
ta_file = 'ta_users.json'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Add handler to output log messages to console
console_handler = logging.StreamHandler()
if debug_mode == False:
    console_handler.setLevel(logging.INFO)
else:
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

# Market variables
valid_bins = [300, 900, 1800, 7200, 14400, 86400]   # Valid candle sizes for API

# Indicator variables
indicators = ['macd']
candle_options = []
for bin_size in valid_bins:
    if bin_size < 7200:
        option = str(int(bin_size / 60)) + ' min'
    elif bin_size < 86400:
        option = str(int(bin_size / (60 * 60))) + ' hour'
    else:
        option = str(int(bin_size / (60 * 60 * 24))) + ' day'
    candle_options.append(option)
logger.debug('candle_options: ' + str(candle_options))


#### HELPER FUNCTIONS ####
def get_list(com, arg=None):
    try:
        if com == 'markets':
            ticker = polo.returnTicker()
            output = []
            if arg:
                for product in ticker:
                    pair = product.split('_')
                    if arg == 'btc':
                        if pair[0] == 'BTC':
                            output.append(pair[1].lower())
                    elif arg == 'eth':
                        if pair[0] == 'ETH':
                            output.append(pair[1].lower())
                    elif arg == 'xmr':
                        if pair[0] == 'XMR':
                            output.append(pair[1].lower())
                    elif arg == 'usdt':
                        if pair[0] == 'USDT':
                            output.append(pair[1].lower())
                output.sort()

            else:
                for product in ticker:
                    pair = product.split('_')
                    if pair[0].lower() not in output:
                        output.append(pair[0].lower())
                output.sort()
            
        else:
            output.append('invalid')

        return output
        

    except Exception:
        logger.exception('Exception while retrieving list data.')
        raise


#### TELEGRAM FUNCTIONS ####
def telegram_build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
        
    return menu


def telegram_button(bot, update):
    # Respond to button presses
    try:
        query = update.callback_query
        telegram_user = query.message.chat_id
        data = query.data

        answer_status = bot.answer_callback_query(query.id)
        logger.debug('[BUTTON] answer_status: ' + str(answer_status))

        data = data.split('-')
        logger.debug('data: ' + str(data))
        #menu = data[0].split('-')
        menu = data[0]
        logger.debug('menu: ' + str(menu))
        selection = data[1]
        logger.debug('selection: ' + str(selection))

        # First tier menu items
        if menu == 'new':
            logger.debug('[BUTTON-new] selection: ' + selection)

            markets = get_list(com='markets', arg=selection)
            logger.debug('[BUTTON-new] markets: ' + str(markets))

            button_list = []
            for market in markets:
                button_list.append(InlineKeyboardButton(market.upper(), callback_data=('sel-' + selection.upper() + '_' + market.upper())))
            
            reply_markup = InlineKeyboardMarkup(telegram_build_menu(button_list, n_cols=4), resize_keyboard=True)
            bot.send_message(chat_id=telegram_user, text='Choose a trade currency:', reply_markup=reply_markup)
        
        elif menu == 'del':
            logger.debug('[BUTTON-del] selection: ' + selection)

            market = selection.split('|')[0]
            indicator = selection.split('|')[1]
            candle = int(selection.split('|')[2])

            logger.debug('Deleting ta_users[' + str(telegram_user) + '][' + market + '][' + indicator + '][' + str(candle) + ']')

            del ta_users[telegram_user][market][indicator][candle]

            delete_message = 'Deleted indicator ' + market.split('_')[1] + market.split('_')[0] + ' ' + candle_options[valid_bins.index(candle)] + ' ' + indicator.upper()

            bot.send_message(chat_id=telegram_user, text=delete_message)
        
        #elif menu == 'my':
            #logger.debug('[BUTTON-my] selection: ' + selection)

        # Second tier menu items
        elif menu == 'sel':
            logger.debug('[BUTTON-sel] selection: ' + selection)
            logger.debug('User: ' + str(telegram_user))
            logger.debug('Selection: ' + str(selection))

            button_list = []
            for indicator in indicators:
                button_list.append(InlineKeyboardButton(indicator.upper(), callback_data=('indic-' + selection + '|' + indicator)))
            
            reply_markup = InlineKeyboardMarkup(telegram_build_menu(button_list, n_cols=1), resize_keyboard=True)
            bot.send_message(chat_id=telegram_user, text='Choose an indicator:', reply_markup=reply_markup)

        # Third tier menu items
        elif menu == 'indic':
            logger.debug('[BUTTON-indic] selection: ' + selection)
            logger.debug('User: ' + str(telegram_user))
            logger.debug('Selection: ' + str(selection))

            market = selection.split('|')[0]
            indicator = selection.split('|')[1]
            
            button_list = []
            for candle_pos in range(0, len(candle_options)):
                button_list.append(InlineKeyboardButton(candle_options[candle_pos], callback_data=('bin-' + market + '|' + indicator + '|' + str(valid_bins[candle_pos]))))
            
            reply_markup = InlineKeyboardMarkup(telegram_build_menu(button_list, n_cols=1), resize_keyboard=True)
            bot.send_message(chat_id=telegram_user, text='Choose a candle length:', reply_markup=reply_markup)

        # Fourth tier menu items
        elif menu == 'bin':
            logger.debug('[BUTTON-bin] selection: ' + selection)
            logger.debug('User: ' + str(telegram_user))
            logger.debug('Selection: ' + str(selection))

            market = selection.split('|')[0]
            indicator = selection.split('|')[1]
            candle = int(selection.split('|')[2])

            # Create dictionary slots for selections if not present
            if market not in ta_users[telegram_user]:
                ta_users[telegram_user][market] = {}
            if indicator not in ta_users[telegram_user][market]:
                ta_users[telegram_user][market][indicator] = {}

            # Add selections to dictionary
            ta_users[telegram_user][market][indicator][candle] = {'state': None, 'last': None}

            products = market.split('_')
            candle_selection = candle_options[valid_bins.index(candle)]

            bot.send_message(chat_id=telegram_user, text=
                             'Added indicator:\n' +
                             products[1] + products[0] + ' ' + candle_selection + ' ' + indicator.upper())
            
    except Exception:
        logger.exception('Exception while responding to button press.')
        raise


def telegram_start(bot, update):
    try:
        telegram_user = update.message.chat_id

        bot.send_message(chat_id=telegram_user, text=
                         'Welcome to TA Alerts bot. Type /connect to begin.')

    except Exception:
        logger.exception('Exception while executing start command.')
        raise


def telegram_connect(bot, update):
    # Add user to file if not already present
    try:
        telegram_user = update.message.chat_id

        connection_successful = False

        if not telegram_check_user(user=telegram_user, reply=False):
            connected_users.append(telegram_user)
            
            #logger.debug('[CONNECT] chat_id: ' + str(telegram_user))
            logger.info('Telegram user connected: ' + str(telegram_user))
            #logger.debug('Connected Users: ' + str(connected_users))

            telegram_message = 'Subscribed to technical analysis alerts.'

            with open(telegram_user_file, 'w') as user_file:
                for x in range(0, len(connected_users)):
                    user_file.write(str(connected_users[x]))
                    if x < (len(connected_users) - 1):
                        user_file.write('\n')
            with open(telegram_user_file, 'r') as user_file:
                users = user_file.read()
            logger.debug('[CONNECT] user_file: ' + users)

            connection_successful = True

        else:
            telegram_message = 'Already subscribed to technical analysis alerts.'
            
        logger.debug('[CONNECT] telegram_message:\n' + telegram_message)

        # Notify user of connection
        bot.send_message(chat_id=telegram_user, text=telegram_message)

        # Send Pepe greeting
        if connection_successful == True:
            ta_users[telegram_user] = {}
            if pepe_greeting == True:
                #bot.send_document(chat_id=telegram_user, document=open(telegram_pepe_file, 'rb'))
                telegram_pepe(bot=bot, requesting_user=telegram_user)

            bot.send_message(chat_id=telegram_user, text=
                             'Hi, I\'m TA Alert Bot! Type /help to see available commands.')
            
    except Exception:
        logger.exception('Exception while connecting Telegram user.')
        raise


def telegram_disconnect(bot, update):
    # Remove user from file if present
    try:
        telegram_user = update.message.chat_id
        print(type(telegram_user))

        if telegram_check_user(user=telegram_user):
            connected_users.remove(telegram_user)

            if telegram_user in ta_users:
                logger.debug('Deleting user: ' + str(telegram_user))
                del ta_users[telegram_user]
            else:
                logger.debug('User not found in dictionary. Skipping deletion.')
            
            #logger.debug('[DISCONNECT] chat_id: ' + str(telegram_user))
            logger.info('Telegram user disconnected: ' + str(telegram_user))
            #logger.debug('Connected Users: ' + str(connected_users))
            
            telegram_message = 'Unsubscribed from technical analysis alerts.'

            with open(telegram_user_file, 'w') as user_file:
                for x in range(0, len(connected_users)):
                    user_file.write(str(connected_users[x]))
                    if x < (len(connected_users) - 1):
                        user_file.write('\n')
            with open(telegram_user_file, 'r') as user_file:
                users = user_file.read()
            logger.debug('[DISCONNECT] user_file: ' + users)

            logger.debug('[DISCONNECT] telegram_message:\n' + telegram_message)

            # Notify user of disconnect
            bot.send_message(chat_id=telegram_user, text=telegram_message)
        
    except Exception:
        logger.exception('Exception while disconnecting Telegram user.')
        raise


def telegram_pepe(bot, update=None, requesting_user=None):
    try:
        if requesting_user:
            telegram_user = requesting_user
        else:
            telegram_user = update.message.chat_id
            
        bot.send_document(chat_id=telegram_user, document=open(telegram_pepe_file, 'rb'))

    except Exception:
        logger.exception('Exception while sending Pepe.')
        raise


def telegram_help(bot, update):
    logger.debug('Help menu requested by user: ' + str(update.message.chat_id))
    try:
        telegram_user = update.message.chat_id

        if telegram_check_user(user=telegram_user):
            #bot.send_message(chat_id=telegram_user, text=help_text)
            help_text = ('Available Commands:\n' +
                         '/connect - Connect to bot\n' +
                         '/disconnect - Disconnect from bot\n' +
                         '/help - This help menu\n' +
                         '/list [command] [argument] (Type /list for more info)\n' +
                         '/newindicator - Add a new indicator alert\n' +
                         '/delindicator - Delete an indicator alert\n' +
                         '/myindicators - List current indicator alerts')
            if pepe_greeting == True:
                help_text = help_text + '\n' + '/pepe - To summon Pepe'
                
            bot.send_message(chat_id=telegram_user, text=help_text)

    except Exception:
        logger.exception('Exception while sending help menu.')
        raise


def telegram_list(bot, update, args):
    try:
        telegram_user = update.message.chat_id
        logger.debug('[/list] args: ' + str(args))

        if telegram_check_user(user=telegram_user):
            arg_length = len(args)
            if arg_length > 1:
                list_com = args[0]
                list_arg = args[1]

                requested_list = get_list(com=list_com, arg=list_arg)
                logger.debug('requested_list: ' + str(requested_list))

                if requested_list[0] != 'invalid':
                    if list_com == 'markets':
                        product_output = ''

                        for product in requested_list:
                            product_output = product_output + product + ', '
                        product_output = product_output.rstrip(', ')

                        bot.send_message(chat_id=telegram_user, text=product_output)
                
                else:
                    # FIX THIS / ADD ROUTING WHEN ONLY COMMAND GIVEN WITHOUT ARGUMENT
                    bot.send_message(chat_id=telegram_user, text=
                                     'Invalid request. Type /list for more information.')

            elif arg_length > 0:
                list_com = args[0]
                requested_list = get_list(com=list_com)
                
                if list_com == 'markets':
                    market_output = ''
                    for market in requested_list:
                        market_output = market_output + market + ', '
                    market_output = market_output.rstrip(', ')

                    bot.send_message(chat_id=telegram_user, text=market_output)
                
            else:
                bot.send_message(chat_id=telegram_user, text=
                                 'Missing Command and Argument:\n' +
                                 '/list [command] [argument]\n' +
                                 'ex. /list markets usdt --> List all X-USDT markets\n' +
                                 '/list [command] to list arguments for a command\n' +
                                 'ex. /list markets --> List all base currency markets')
            
    except Exception:
        logger.exception('Exception while handling list command.')
        raise


def telegram_newindicator(bot, update):
    # Add a new indicator
    try:
        telegram_user = update.message.chat_id

        logger.debug('User ' + str(telegram_user) + ' requesting new indicator.')

        if telegram_check_user(user=telegram_user):
            button_list = [
                InlineKeyboardButton('X-BTC', callback_data='new-btc'),
                InlineKeyboardButton('X-ETH', callback_data='new-eth'),
                InlineKeyboardButton('X-XMR', callback_data='new-xmr'),
                InlineKeyboardButton('X-USDT', callback_data='new-usdt')
            ]
            reply_markup = InlineKeyboardMarkup(telegram_build_menu(button_list, n_cols=2), resize_keyboard=True)
            bot.send_message(chat_id=telegram_user, text='Choose a market:', reply_markup=reply_markup)

    except Exception:
        logger.exception('Exception while adding new indicator.')
        raise


def telegram_delindicator(bot, update):
    # Delete an indicator
    try:
        telegram_user = update.message.chat_id

        logger.debug('User ' + str(telegram_user) + ' requesting indicator deletion.')

        if telegram_check_user(user=telegram_user):
            button_list = []
            for market in ta_users[telegram_user]:
                for indicator in ta_users[telegram_user][market]:
                    for bin_size in ta_users[telegram_user][market][indicator]:
                        button_text =  market.split('_')[1] + market.split('_')[0] + ' ' + candle_options[valid_bins.index(bin_size)] + ' ' + indicator.upper()
                        button_callback = 'del-' + market + '|' + indicator + '|' + str(bin_size)
                        button_list.append(InlineKeyboardButton(button_text, callback_data=button_callback))
            
            reply_markup = InlineKeyboardMarkup(telegram_build_menu(button_list, n_cols=1), resize_keyboard=True)
            bot.send_message(chat_id=telegram_user, text='Choose an indicator to delete:', reply_markup=reply_markup)

    except Exception:
        logger.exception('Exception while deleting indicator.')
        raise


def telegram_myindicators(bot, update):
    # List user's current indicators
    try:
        telegram_user = update.message.chat_id

        logger.debug('User ' + str(telegram_user) + ' requesting indicator subscriptions.')

        if telegram_check_user(user=telegram_user):
            current_indicators = 'Current indicator subscriptions:\n\n'
            for market in ta_users[telegram_user]:
                #current_indicators = current_indicators + market.split('_')[1] + market.split('_')[0]# + ':\n'
                for indicator in ta_users[telegram_user][market]:
                    for bin_size in ta_users[telegram_user][market][indicator]:
                        current_indicators = (current_indicators +
                                              market.split('_')[1] + market.split('_')[0] +
                                              ' - ' + candle_options[valid_bins.index(bin_size)] +
                                              ' ' + indicator.upper() + '\n')
            current_indicators.rstrip('\n')
            
            bot.send_message(chat_id=telegram_user, text=current_indicators)

    except Exception:
        logger.exception('Exception while listing current indicators.')
        raise


def telegram_check_user(user, reply=True):
    try:
        if user in ta_users:
            return True

        elif reply == True:
            updater.bot.send_message(chat_id=user, text=
                             'Not in list of active users.\n' +
                             'Type /connect to connect to alert bot.')
            return False

    except Exception:
        logger.exception('Exception while checking user agains\'t connected user list.')
        raise


def telegram_unknown(bot, update):
    # Respond to unknown command
    try:
        telegram_user = update.message.chat_id
        bot.send_message(chat_id=telegram_user, text='Unknown command. Type /help for a full list of commands.')

    except Exception:
        logger.exception('Exception while handling unknown command.')
        raise


def telegram_error(bot, update, error):
    try:
        raise error
    except Unauthorized:
        # remove update.message.chat_id from conversation list
        pass
    except BadRequest:
        # handle malformed requests - read more below!
        pass
    except TimedOut:
        # handle slow connection problems
        logger.debug('Telegram exception TimedOut.')
        print(update)
        print(error)
        print('TIMED OUT')
        time.sleep(5)
    except NetworkError:
        # handle other connection problems
        pass
    except ChatMigrated as e:
        # the chat_id of a group has changed, use e.new_chat_id instead
        pass
    except TelegramError:
        # handle all other telegram related errors
        pass


#### ANALYSIS FUNCTIONS ####
# Get candle data
def get_candles(product, time_bin):
    try:
        if time_bin in valid_bins:
            if time_bin == 300:
                start_time = time.time() - (300 * 52)
            elif time_bin == 900:
                start_time = time.time() - (900 * 52)
            elif time_bin == 1800:
                start_time = time.time() - (1800 * 52)
            elif time_bin == 7200:
                start_time = time.time() - (7200 * 52)
            elif time_bin == 14400:
                start_time = time.time() - (14400 * 52)
            elif time_bin == 86400:
                start_time = time.time() - (86400 * 52)
            #end_time = time.time()
            
            data = polo.returnChartData(product, period=time_bin, start=start_time)#, end=end_time)
        
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
                'product': product,
                'time_bin': time_bin
                }

            return candle_data

        else:
            logger.error('Invalid time bin given to get_candles() function.')

    except Exception:
        logger.exception('Exception while retrieving candle data.')
        raise


# Moving-Average Convergence/Divergence
def calc_macd(data, long, short, signal, simple_output=False):
    logger.debug('Calculating MACD.')
    logger.debug('Long: ' + str(long))
    logger.debug('Short: ' + str(short))
    logger.debug('Signal: ' + str(signal))
    
    try:
        macd, signal, histogram = talib.abstract.MACD(data, long, short, signal, price='close')

        macd_current = macd[-1]
        signal_current = signal[-1]
        histogram_current = histogram[-1]

        macd_values = {'macd': macd_current,
                       'signal': signal_current,
                       'histogram': histogram_current}

        logger.debug('macd: ' + str(macd_values['macd']))
        logger.debug('signal: ' + str(macd_values['signal']))
        logger.debug('histogram: ' + str(macd_values['histogram']))

        if simple_output == True:
            output = {}
            if macd_values['histogram'] > 0:
                result = 'ABOVE'
            else:
                result = 'BELOW'
            output['cross'] = result

            if macd_values['macd'] > 0:
                result = 'ABOVE'
            else:
                result = 'BELOW'
            output['zero'] = result

        else:
            output = macd_values

        return output

    except Exception:
        logger.exception('Exception while calculating MACD.')
        raise


if __name__ == '__main__':
    # Get config file(s) and set program values from it/them
    config = configparser.ConfigParser()

    if not os.path.isfile(telegram_config_file):
        logger.error('No Telegram config file found! Must create \".telegram.ini\". Exiting.')
        sys.exit(1)
    else:
        logger.info('Found Telegram config file.')
    
    # Set Telegram token
    config.read(telegram_config_file)
    if debug_mode == False:
        telegram_token = config['telegram']['token']
    else:
        telegram_token = config['telegram_test']['token']
    logger.debug('telegram_token: ' + str(telegram_token))

    connected_users = []
    ta_users = {}

    """
    if os.path.isfile(telegram_user_file):
        logger.info('Found Telegram user file. Loading connected users.')
        with open(telegram_user_file, 'r') as user_file:
            #user_string = user_file.read()
            user_list = user_file.read().split('\n')
        #user_list = user_string.split('\n')
        for user in user_list:
            #if user != '' and connected_users.count(int(user)) == 0:
            if user != '' and int(user) not in connected_users:
                connected_users.append(int(user))
                ta_users[int(user)] = {}
                logger.info('Connected User: ' + user)
    
    else:
        logger.info('No Telegram user file found. Creating empty file.')
        with open(telegram_user_file, 'w') as user_file:
            pass
    logger.debug('connected_users: ' + str(connected_users))
    """

    if os.path.isfile(ta_file):
        logger.info('Found saved ta_users file. Loading connected users and indicators.')
        with open(ta_file, 'r') as file:
            ta_users = json.load(file)

        logger.debug('Round #1: ta_users str-->int conversion')
        for user in ta_users:
            temp_user = int(user)
            temp_dict = ta_users[user]
            del ta_users[user]
            ta_users[temp_user] = temp_dict
            
        for user in ta_users:
            for market in ta_users[user]:
                for indicator in ta_users[user][market]:
                    for bin_size in ta_users[user][market][indicator]:
                        logger.debug('bin_size: ' + str(bin_size))
                        temp_bin_size = int(bin_size)
                        logger.debug('temp_bin_size: ' + str(temp_bin_size))
                        temp_dict = ta_users[user][market][indicator][bin_size]
                        del ta_users[user][market][indicator][bin_size]
                        ta_users[user][market][indicator][temp_bin_size] = temp_dict

        logger.debug('Round #2: ta_users str-->int conversion')
        for user in ta_users:
            temp_user = int(user)
            temp_dict = ta_users[user]
            del ta_users[user]
            ta_users[temp_user] = temp_dict
            
        for user in ta_users:
            for market in ta_users[user]:
                for indicator in ta_users[user][market]:
                    for bin_size in ta_users[user][market][indicator]:
                        logger.debug('bin_size: ' + str(bin_size))
                        temp_bin_size = int(bin_size)
                        logger.debug('temp_bin_size: ' + str(temp_bin_size))
                        temp_dict = ta_users[user][market][indicator][bin_size]
                        del ta_users[user][market][indicator][bin_size]
                        ta_users[user][market][indicator][temp_bin_size] = temp_dict
                        
        if debug_mode == True:
            print('Converted bin sizes from str --> int')
            pprint(ta_users)
            print()
            time.sleep(5)
            print('Loaded ta_users file:')
            pprint(ta_users)
            print()

    else:
        logger.info('No user saved indicators file found. Starting fresh.')

    updater = Updater(token=telegram_token)

    # Commands
    updater.dispatcher.add_handler(CommandHandler('start', telegram_start))
    updater.dispatcher.add_handler(CommandHandler('connect', telegram_connect))
    updater.dispatcher.add_handler(CommandHandler('disconnect', telegram_disconnect))
    updater.dispatcher.add_handler(CommandHandler('pepe', telegram_pepe))
    updater.dispatcher.add_handler(CommandHandler('help', telegram_help))
    updater.dispatcher.add_handler(CommandHandler('list', telegram_list, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('newindicator', telegram_newindicator))
    updater.dispatcher.add_handler(CommandHandler('delindicator', telegram_delindicator))
    updater.dispatcher.add_handler(CommandHandler('myindicators', telegram_myindicators))
    # Callback data from button presses
    updater.dispatcher.add_handler(CallbackQueryHandler(telegram_button))
    # Unknown command handling
    updater.dispatcher.add_handler(MessageHandler(Filters.command, telegram_unknown))
    # Error handling
    updater.dispatcher.add_error_handler(telegram_error)

    #start_polling(poll_interval=0.0, timeout=10, network_delay=None, clean=False, bootstrap_retries=0, read_latency=2.0, allowed_updates=None)
    #updater.start_polling(timeout=20, bootstrap_retries=5, read_latency=20)
    updater.start_polling()

    # Poloniex API
    polo = poloniex.Poloniex()

    for user in ta_users:
        #updater.bot.send_message(chat_id=user, text=
                                 #'Program was restarted. Indicators set previously were deleted and need to be added again manually. Sorry for the inconvenience.')
        updater.bot.send_message(chat_id=user, text=
                                 'Program restarted. Your indicators have been reloaded. If you experience any issues, please report them to the developer. Thanks.')

    loop_count = 0
    while(True):
        try:
            loop_count += 1
            logger.debug('loop_count: ' + str(loop_count))
            
            if debug_mode:
                print('BEGINNING LOOP')
                print('ta_users:')
                pprint(ta_users)
                print()
                
            # Determine required candle data
            user_requests = {}
            for user in ta_users:
                for market in ta_users[user]:
                    if market not in user_requests:
                        #user_requests[market] = []
                        user_requests[market] = {}
                    for indicator in ta_users[user][market]:
                        for bin_size in ta_users[user][market][indicator]:
                            if bin_size not in user_requests[market]:
                                user_requests[market][bin_size] = {}

            if debug_mode:
                print('REQUESTS RETRIEVED')
                print('user_requests:')
                pprint(user_requests)
                print()
            
            # Get candle data
            for market in user_requests:
                for bin_size in user_requests[market]:
                    logger.debug('Retrieving candles: ' + market + ' / ' + str(bin_size))
                    user_requests[market][bin_size]['candles'] = get_candles(product=market, time_bin=bin_size)
                    time.sleep(1)

            if debug_mode:
                print('CANDLES GATHERED')
                #print('user_requests:')
                #pprint(user_requests)
                print()
            
            # Perform technical analysis
            for user in ta_users:
                test_user = user
                for market in ta_users[user]:
                    for indicator in ta_users[user][market]:
                        for bin_size in ta_users[user][market][indicator]:
                            logger.debug('Performing analysis: ' + market + ' / ' + indicator + ' / ' + str(bin_size))
                            if indicator == 'macd':
                                ta_users[user][market][indicator][bin_size]['state'] = calc_macd(data=user_requests[market][bin_size]['candles'],
                                                                                                 long=26, short=10, signal=9,
                                                                                                 simple_output=True)
                                if ta_users[user][market][indicator][bin_size]['last'] == None:
                                    ta_users[user][market][indicator][bin_size]['last'] = {}
                                    cross_val = ta_users[user][market][indicator][bin_size]['state']['cross']
                                    ta_users[user][market][indicator][bin_size]['last']['cross'] = cross_val
                                    zero_val = ta_users[user][market][indicator][bin_size]['state']['zero']
                                    ta_users[user][market][indicator][bin_size]['last']['zero'] = zero_val

            if debug_mode:
                print('ANALYSIS COMPLETE')
                print('ta_users:')
                pprint(ta_users)
                print()

            # Check for alerts
            telegram_alerts = {}
            for user in ta_users:
                telegram_alerts[user] = []
                for market in ta_users[user]:
                    for indicator in ta_users[user][market]:
                        for bin_size in ta_users[user][market][indicator]:
                            if ta_users[user][market][indicator][bin_size]['state']['cross'] != ta_users[user][market][indicator][bin_size]['last']['cross']:
                                alert = candle_options[valid_bins.index(bin_size)] + ' ' + indicator.upper() + '-Signal crossed ' + ta_users[user][market][indicator][bin_size]['state']['cross']
                                telegram_alerts[user].append(alert)
                                cross_val = ta_users[user][market][indicator][bin_size]['state']['cross']
                                ta_users[user][market][indicator][bin_size]['last']['cross'] = cross_val

                            if ta_users[user][market][indicator][bin_size]['state']['zero'] != ta_users[user][market][indicator][bin_size]['last']['zero']:
                                alert = candle_options[valid_bins.index(bin_size)] + ' ' + indicator.upper() + '-Zero crossed ' + ta_users[user][market][indicator][bin_size]['state']['zero']
                                telegram_alerts[user].append(alert)
                                zero_val = ta_users[user][market][indicator][bin_size]['state']['zero']
                                ta_users[user][market][indicator][bin_size]['last']['zero'] = zero_val

            if debug_mode:
                print('ALERTS COMPILED')
                print()

            # Send alerts to users
            for user in telegram_alerts:
                for alert in telegram_alerts[user]:
                    logger.debug('Alert for user ' + str(user) + ': ' + alert)
                    updater.bot.send_message(chat_id=user, text=alert)

            if debug_mode:
                print('ALERTS SENT')
                print()

            time.sleep(loop_time)

        except Exception as e:
            logger.exception('Exception raised.')
            logger.exception(e)

        except KeyboardInterrupt:
            logger.debug('Exit signal received.')
            logger.debug('Sending shutdown warning to users.')
            for user in ta_users:
                updater.bot.send_message(chat_id=user, text=
                                         'TA Alerts is going down for maintenance. Your indicators will be saved. A message will be sent when TA Alerts is restarted. Sorry for any inconvenience.')
            logger.debug('Stopping Telegram updater.')
            updater.stop()
            logger.debug('Saving user indicators to file.')
            with open(ta_file, mode='w') as file:
                json.dump(ta_users, file, sort_keys=True, indent=4, ensure_ascii=False)
            sys.exit()
