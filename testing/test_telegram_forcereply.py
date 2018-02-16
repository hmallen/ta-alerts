import argparse
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
#from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, Updater, Filters
import time

telegram_user = 382606465  # @hmallen


#### TELEGRAM FUNCTIONS ####
def telegram_build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
        
    return menu


# UNUSED
def telegram_build_callback(data):
    return_value = json.dumps(data)
    if len(return_value) > 64:
        #raise TelegramCallbackError('Callback data is larger than 64 bytes.')
        logger.error('Callback data is larger than 64 bytes.')
    return return_value


def telegram_button(bot, update):
    # Respond to button presses
    try:
        query = update.callback_query
        telegram_user = query.message.chat_id
        data = query.data

        print('QUERY: ', query)
        print()
        print('USER: ', telegram_user)
        print('DATA: ', data)
        print()

        data = data.split('_')
        logger.debug('data: ' + str(data))
        menu = data[0].split('-')
        logger.debug('menu: ' + str(menu))
        selection = data[1]
        logger.debug('selection: ' + str(selection))

        if menu[0] == 'new':
            print('WOOHOO')
        
        elif menu[0] == 'del':
            print('EH...')
        
        elif menu[0] == 'my':
            print('EH...')

        #reply_markup = ReplyKeyboardRemove()
        #bot.send_message(chat_id=telegram_user, text='Hello, world!', reply_markup=reply_markup)

    except Exception:
        logger.exception('Exception while responding to button press.')
        raise


def telegram_newindicator(bot, update):
    # Add a new indicator
    try:
        telegram_user = update.message.chat_id

        if telegram_check_user(telegram_user):
            button_list = [
                InlineKeyboardButton('X-BTC', callback_data='new-market_btc'),
                InlineKeyboardButton('X-ETH', callback_data='new-market_eth'),
                InlineKeyboardButton('X-XMR', callback_data='new-market_xmr'),
                InlineKeyboardButton('X-USDT', callback_data='new-market_usdt')
            ]
            reply_markup = InlineKeyboardMarkup(telegram_build_menu(button_list, n_cols=2), resize_keyboard=True)
            bot.send_message(chat_id=telegram_user, text='Choose a market:', reply_markup=reply_markup)
            #update.message.reply_text(text='Choose a market:', reply_markup=reply_markup)

    except Exception:
        logger.exception('Exception while adding new indicator.')
        raise


def telegram_error(bot, update, error):
    #Log errors caused by updates
    logger.warning('Update "%s" caused error "%s"', update, error)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('../config/config.ini')

    telegram_token = config['telegram_test']['token']

    updater = Updater(token=telegram_token)

    # Commands
    updater.dispatcher.add_handler(CommandHandler('newindicator', telegram_newindicator))
    # Callback data from button presses
    updater.dispatcher.add_handler(CallbackQueryHandler(telegram_button))
    # Error handling
    updater.dispatcher.add_error_handler(telegram_error)

    updater.start_polling(timeout=20)
