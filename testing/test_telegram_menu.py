import configparser
import logging
import os
import poloniex
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup#, ReplyKeyboardRemove, ParseMode
from telegram.ext import Updater, CommandHandler, ConversationHandler, RegexHandler, MessageHandler
import time

"""
def help_command(message):
   keyboard = telebot.types.InlineKeyboardMarkup()
   keyboard.add(
       telebot.types.InlineKeyboardButton(
           ‘Message the developer’, url='telegram.me/artiomtb'
       )
   )
   bot.send_message(
       message.chat.id,
       '1) To receive a list of available currencies press /exchange.\n' +
       '2) Click on the currency you are interested in.\n' +
       '3) You will receive a message containing information regarding the source and the target currencies, ' +
       'buying rates and selling rates.\n' +
       '4) Click “Update” to receive the current information regarding the request. ' +
       'The bot will also show the difference between the previous and the current exchange rates.\n' +
       '5) The bot supports inline. Type @<botusername> in any chat and the first letters of a currency.',
       reply_markup=keyboard
   )

button_list = [
                telegram.InlineKeyboardButton("col1", callback_data='one'),
                telegram.InlineKeyboardButton("col2", callback_data='two'),
                telegram.InlineKeyboardButton("row 2", callback_data='three')
                ]
reply_markup = telegram.InlineKeyboardMarkup(util.helpers.build_menu(button_list, n_cols=2))
bot.send_message(chat_id=telegram_user, text='A two-column menu', reply_markup=reply_markup)
"""

telegram_user = 382606465  # @hmallen
loop_time = 30

log_file = 'logs/test_log.log'
telegram_config_file = '../config/config.ini'
telegram_pepe_file = '../resources/matrix_pepe.gif'

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


def build_menu(buttons, n_cols=1, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]

    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    return menu


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


def telegram_menu(bot, update):
    try:
        telegram_user = update.message.chat_id

        button_list = [InlineKeyboardButton("col1", callback_data='one'),
                       InlineKeyboardButton("col2", callback_data='two'),
                       InlineKeyboardButton("row 2", callback_data='three')]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
        
        bot.send_message(chat_id=telegram_user, text='Make a selection:', reply_markup=reply_markup)
        

    except Exception:
        logger.exception('Exception while sending menu.')
        raise


def telegram_error(bot, update, error):
    #Log errors caused by updates
    logger.warning('Update "%s" caused error "%s"', update, error)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(telegram_config_file)
    telegram_token = config['telegram_test']['token']
    
    updater = Updater(token=telegram_token)

    updater.dispatcher.add_handler(CommandHandler('pepe', telegram_pepe))
    updater.dispatcher.add_handler(CommandHandler('menu', telegram_menu))

    updater.dispatcher.add_error_handler(telegram_error)

    updater.start_polling(timeout=10)

    while(True):
        try:
            logger.debug('Hello, world!')
            
            #time.sleep(loop_time)
            time.sleep(120)

        except Exception as e:
            logger.exception('Exception raised.')
            logger.exception(e)
            updater.stop()
            sys.exit(1)

        except KeyboardInterrupt:
            logger.info('Exit signal received.')
            updater.stop()
            sys.exit()
