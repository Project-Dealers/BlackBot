#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
import requests
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, ConversationHandler)

try:
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
        TOKEN = config['bot_token']
        API_URL = config['api_url']
except FileNotFoundError:
    print('Please provide the following credentials')
    TOKEN = input('Telegram bot API token: ')
    API_URL = input('API URL: ')
    config = {
        'bot_token': TOKEN,
        'api_url': API_URL
    }
    with open('config.json', 'w', encoding='utf-8') as outf:
        json.dump(config, outf, indent=4)


credentials = {}
APIKEY, SEARCHTYPE, PHONE, PASSPORTSERIES,\
        PASSPORTNUMBER, OKPO, CARDID = range(7)


def search(params):
    r = requests.post(API_URL, data=params).json()
    results = False
    for key, value in r.items():
        if not (('result' in value) and (value['result'] == 'not found')):
            results = value
            break
    if results:
        text = 'Результаты поиска:\n'
        for result in results:
            text = f'''Полное имя: {result['full_name']}
Дата владельца: {result['owner_date']}
Причина внесения: {result['reason']}\n'''
    else:
        text = 'Ничего не найдено — попробуйте найти по другим параметрам'
    return text


def start(update, context):
    first_name = update.message.from_user.first_name
    reply_keyboard = [['Проверить']]
    update.message.reply_text(
        'Добро пожаловать, {}!\n'
        'Я помогу вам проверить ваши '
        'данные на наличие в чёрном списке'.format(first_name),
        reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                         one_time_keyboard=True,
                                         resize_keyboard=True)
    )


def check(update, context):
    update.message.reply_text('Укажите API-ключ')
    return APIKEY


def apikey(update, context):
    user_id = update.message.from_user.id
    credentials[user_id] = {}
    key = update.message.text
    credentials[user_id]['key'] = key
    reply_keyboard = [['Номер телефона', 'Паспорт', 'ОКПО', 'ID карты']]
    update.message.reply_text(
        'Выберите, по каким параметрам будем искать',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                         one_time_keyboard=True,
                                         resize_keyboard=True))
    return SEARCHTYPE


def search_type(update, context):
    text = update.message.text
    if text == 'Номер телефона':
        reply = 'Укажите номер телефона (в формате +380XXXXXXXXX)'
        res = PHONE
    elif text == 'Паспорт':
        reply = 'Укажите серию паспорта'
        res = PASSPORTSERIES
    elif text == 'ОКПО':
        reply = 'Укажите общественный классификатор предприятий и организаций'
        res = OKPO
    elif text == 'ID карты':
        reply = 'Укажите ID карты'
        res = CARDID
    update.message.reply_text(reply, reply_markup=ReplyKeyboardRemove())
    return res


def phone(update, context):
    reply_keyboard = [['Проверить']]
    user_id = update.message.from_user.id
    text = update.message.text
    credentials[user_id]['mobile_phone'] = text
    results = search(credentials[user_id])
    update.message.reply_text(
        results,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                         one_time_keyboard=True,
                                         resize_keyboard=True))
    return ConversationHandler.END


def passport_series(update, context):
    user_id = update.message.from_user.id
    text = update.message.text
    credentials[user_id]['passport_series'] = text
    update.message.reply_text('Укажите номер паспорта')
    return PASSPORTNUMBER


def passport_number(update, context):
    reply_keyboard = [['Проверить']]
    user_id = update.message.from_user.id
    text = update.message.text
    credentials[user_id]['passport_number'] = text
    results = search(credentials[user_id])
    update.message.reply_text(
        results,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                         one_time_keyboard=True,
                                         resize_keyboard=True))
    return ConversationHandler.END


def okpo(update, context):
    reply_keyboard = [['Проверить']]
    user_id = update.message.from_user.id
    text = update.message.text
    credentials[user_id]['okpo'] = text
    results = search(credentials[user_id])
    update.message.reply_text(
        results,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                         one_time_keyboard=True,
                                         resize_keyboard=True))
    return ConversationHandler.END


def card_id(update, context):
    reply_keyboard = [['Проверить']]
    user_id = update.message.from_user.id
    text = update.message.text
    credentials[user_id]['number_id_card'] = text
    results = search(credentials[user_id])
    update.message.reply_text(
        results,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                         one_time_keyboard=True,
                                         resize_keyboard=True))
    return ConversationHandler.END


def cancel(update, context):
    reply_keyboard = [['Проверить']]
    update.message.reply_text(
        'Операция поиска отменена',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                         one_time_keyboard=True))
    return ConversationHandler.END


updater = Updater(TOKEN, use_context=True)

dp = updater.dispatcher
conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('check', check),
            MessageHandler(Filters.regex('Проверить'), check)
        ],

        states={
            APIKEY: [MessageHandler(Filters.text, apikey)],
            SEARCHTYPE: [MessageHandler(Filters.regex(
                '^(Номер телефона|Паспорт|ОКПО|ID карты)$'
            ), search_type)],
            PHONE: [MessageHandler(Filters.text, phone)],
            PASSPORTSERIES: [MessageHandler(Filters.text, passport_series)],
            PASSPORTNUMBER: [MessageHandler(Filters.text, passport_number)],
            OKPO: [MessageHandler(Filters.text, okpo)],
            CARDID: [MessageHandler(Filters.text, card_id)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
dp.add_handler(CommandHandler("start", start))
dp.add_handler(conv_handler)

updater.start_polling(poll_interval=2)
