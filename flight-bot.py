import logging, re, codecs
from multiprocessing import context
from telegram.ext import filters, ContextTypes, Updater, CommandHandler, MessageHandler, ApplicationBuilder, ConversationHandler
import requests
import json
from datetime import datetime, timedelta
from dateutil import parser
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, _update
import json
from datetime import datetime, timedelta
from dateutil.parser import parse
from dateutil.rrule import rrule, rruleset, DAILY, WEEKLY, MO, TU, WE, TH, FR, SA, SU

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define global variables for aviasales API token and marker
AVIASALES_API_TOKEN = 'c70dab9255f2dfc1ea4b62be614af2c2'
AVIASALES_API_MARKER = '435077'

# Define global variables for Telegram bot token
TELEGRAM_BOT_TOKEN = '5985338481:AAGymCDgbI59WAtspbfKk4SEYtIzdiKZ4IY'

# Define conversation states
CURRENCY, DEPARTURE_CITY, DESTINATION_CITY, ONEWAY_ROUNDTRIP, DEPARTURE_DATE, DESTINATION_DATE = range(6)

"""
def get_reference_info():
    global cities
    url = "https://api.travelpayouts.com/aviasales_resources/v3/cities.json?locale=en"
    cities = requests.get(url)
    return cities
"""
def know_city_by_code(city_code):
    with open('cities.json', 'rb') as file:
        data = file.read().decode('utf-8')
        cities = json.loads(data)
    for item in cities:
        if item['code'] == city_code:
            city_name = item['name']
            return city_name
        
def know_code_by_city(city_name):
    with open('cities.json', 'rb') as file:
        data = file.read().decode('utf-8')
        cities = json.loads(data)
        city_code_name = ''
    for item in cities:
        if item['name'].lower() == city_name.lower():
            city_code_name = item['code']
            return city_code_name
    if not city_code_name:
        logger.exception("There is no such city {city_name}")
        return False

def know_country_emoji_flag_by_city(city_code):
    with open('cities.json', 'rb') as file:
        data = file.read().decode('utf-8')
        cities = json.loads(data)
        for item in cities:
            if item['code'] == city_code:
                country_code = item['country_code']
    with open('emojiflags.json', 'rb') as file:
        data = file.read().decode('utf-8')
        countries = json.loads(data)
        for item in countries:
            if item['code'] == country_code:
                emoji = item['unicode']
                emoji_str = ''.join(['\\U{:0>8}'.format(x[2:]) for x in emoji.split()])
                return emoji_str

def currency_verifier(currency_code):
    with open("currencies.json", 'rb') as file:
        data = file.read().decode('utf-8')
        currency_list = json.loads(data)
    currency_name = ''
    for item in currency_list:
        if item['cc'].lower() == currency_code.lower():
            currency_name = item['name']
            print(f'For the {currency_code} currency code the {currency_name} was found')
            return True, 
    if not currency_name:
        logger.exception("There is no such currency {currency_code}")
        return False
    
def minutes_to_hours(minutes):
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours:02d}:{minutes:02d}"
        
#calculating days of a week
def calendar (weekday) -> None:
    date1 = departure_date
    date2 = destination_date

    result = rrule(
        DAILY,
        byweekday=(weekday),
        dtstart=parse(date1),
        until=parse(date2)
        )
    
    list_of_selected_weekdays = list(result)
    good_list_of_selected_weekdays = []
    for x in list_of_selected_weekdays:
        x = x.date()
        x = x.strftime('%Y-%m-%d')
        good_list_of_selected_weekdays.append(x)
    # TO DO list lenght can be different , neet make them equal
    return good_list_of_selected_weekdays

    
def is_valid_date(date_string):
    pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    match = pattern.match(date_string)
    if match:
        return True
    else:
        return False
    

def get_weekend_days(start_date=datetime.today(), num_days=180):
    global weekends
    end_date = start_date + timedelta(days=num_days)
    weekends = rruleset()
    weekends.rrule(rrule(freq=WEEKLY, byweekday=(SA, SU), dtstart=start_date))
    weekends.rrule(rrule(freq=WEEKLY, byweekday=(SA, SU), dtstart=start_date + timedelta(days=7)))
    weekends.between(start_date, end_date, inc=True)
    return list(weekends)


# Define function for sending flight offers
def send_flight_offers(flight_offers):
    if flight_offers is None:
        message = "No flight offers found."
    else:
        #get_reference_info()
        message = ""
        for offer in flight_offers:
            #send round trip flights
            if not oneway_or_roundtrip_option:
                origin = offer["origin"]
                departure_city_name = know_city_by_code(origin)
                destination = offer["destination"]
                destination_city_name = know_city_by_code(destination)
                origin_airport = offer["origin_airport"]
                destination_airport = offer["destination_airport"]
                price = offer["price"]
                airline = offer["airline"]
                flight_number = offer["flight_number"]
                transfers = offer["transfers"]
                return_transfers = offer["return_transfers"]
                link = offer["link"]
                departure_time = datetime.fromisoformat(offer["departure_at"]).strftime("%Y-%m-%d %H:%M:%S")
                return_time = datetime.fromisoformat(offer["return_at"]).strftime("%Y-%m-%d %H:%M:%S")

                # Detrmine destination country emoji flag
                emoji = know_country_emoji_flag_by_city(destination)
                decoded_emoji = codecs.decode(emoji, 'unicode_escape')

                message += f"\U0001F4CC {departure_city_name} ({origin_airport}) to {decoded_emoji} {destination_city_name} ({destination_airport}) with {airline} {flight_number}\n"
                #message += f"\U0001F4B2 Departure: {departure_city_name} Destination {destination_city_name}\n"
                message += f"\U0001F6EB Departure: {departure_time}\n"
                message += f"\U0001F6EC Return: {return_time}\n"
                message += f"\U000027A1 Connections: {transfers}\n"
                message += f"\U00002B05 Connections: {return_transfers}\n"
                #message += f"Link: {link}\n"
                message += f"\U0001F4B5 Price: {price} {user_currency}\n\n"
            # Send one way flights
            else:
                origin = offer["origin"]
                departure_city_name = know_city_by_code(origin)
                destination = offer["destination"]
                destination_city_name = know_city_by_code(destination)
                origin_airport = offer["origin_airport"]
                destination_airport = offer["destination_airport"]
                price = offer["price"]
                airline = offer["airline"]
                flight_number = offer["flight_number"]
                transfers = offer["transfers"]
                duration = offer["duration"]
                good_looking_duration = minutes_to_hours(duration)
                link = offer["link"]
                departure_time = datetime.fromisoformat(offer["departure_at"]).strftime("%Y-%m-%d %H:%M:%S")

                # Detrmine destination country emoji flag
                emoji = know_country_emoji_flag_by_city(destination)
                decoded_emoji = codecs.decode(emoji, 'unicode_escape')

                message += f"\U0001F4CC {departure_city_name} ({origin_airport}) to {decoded_emoji} {destination_city_name} ({destination_airport}) with {airline} {flight_number}\n"
                #message += f"\U0001F4B2 Departure: {departure_city_name} Destination {destination_city_name}\n"
                message += f"\U0001F6EB Departure: {departure_time}\n"
                message += f"\U000023F3 Duration: {good_looking_duration}\n"
                message += f"\U000027A1 Connections: {transfers}\n"
                #message += f"Link: {link}\n"
                message += f"\U0001F4B5 Price: {price} {user_currency}\n\n"
    return message


# Define function for getting round trip flight offers
def get_flight_offers(origin,destination,depart_date,return_date, isOneWay):
    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
    params = {
        "origin": origin,
        "destination": destination,
        "departure_at": depart_date,
        "return_at": return_date,
        "unique" : "true",
        "sorting" : "price",
        "direct" : "false",
        "currency" : user_currency,
        "market" : "cz",
        "limit" : 10,
        "page" : 1,
        "one_way" : isOneWay,
        "token" : AVIASALES_API_TOKEN 
    }
    response = requests.get(url, params=params)
    logger.info(response.status_code, depart_date, return_date)
    
    if response.status_code != 200:
        return None

    data = response.json()

    success = data['success']
    data_list = data['data']
    currency = data['currency']

    return data_list


# Define function for starting the conversation with the user
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the Aviasales bot. Please type the currency code in the format 'USD' to get started.")
    return CURRENCY

async def set_currency(update, context):
    global user_currency

    verification = False
    while not verification:
        user_currency = update.message.text.upper()
        verification = currency_verifier(user_currency)
        if verification:
            print(f'The currency provided correctly')
            break

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text=f"The currency code {user_currency} is not valid.\nPlease type the currency code in the format 'USD' to proceed")
        update = await context.bot.get_updates(update_id=update.update_id+1)

    #TODO check if provided currency is a text and not a document, media etc

    # Send a message with the city options as buttons
    reply_keyboard = [['Prague', 'Vienna', 'Munich'], ['Madrid', 'Barcelona', 'Rome']]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True, selective=True, input_field_placeholder='Choose a departure city')
    await context.bot.send_message(chat_id=update.effective_chat.id,
                            text='Choose a departure city:',
                            reply_markup=reply_markup)
    return DEPARTURE_CITY

# Define function for handling input of departure city
async def set_departure_city(update, context):
    global departure_city_code

    departure_city_code = ''
    while not departure_city_code:
        departure_city = update.message.text
        departure_city_code = know_code_by_city(departure_city)
        if departure_city_code:
            print(f'The departure city provided correctly')
            break

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text=f"The departure city {departure_city} is not valid or it doesn't have an airport.\nPlease type the correct city to proceed") 
        update = await context.bot.get_updates(update_id=update.update_id+1)               

    await update.message.reply_text("Enter the destination city, use /skip command if you don't want to cpecify the destination city",                                 
                            reply_markup=ReplyKeyboardRemove())
    return DESTINATION_CITY

# Define function for handling input of destination city
async def set_destination_city(update, context):
    global destination_city_code

    destination_city_code = ''
    while not destination_city_code:
        destination_city = update.message.text
        destination_city_code = know_code_by_city(destination_city)
        if destination_city_code:
            print(f'The destination city provided correctly')
            break       

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text=f"The destination city {destination_city} is not valid or it doesn't have an airport.\nPlease type the correct city to proceed or use /skip command if you don't want to cpecify the destination city") 
        update = await context.bot.get_updates(update_id=update.update_id+1)           

    #await context.bot.send_message(chat_id=update.effective_chat.id, text="Enter the departure date in the format YYYY-MM-DD")
    
    reply_keyboard = [['One way', 'Round trip']]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True, selective=True, input_field_placeholder='Choose weather the flight is one way or a round trip')
    await context.bot.send_message(chat_id=update.effective_chat.id,
                            text='Choose if the flight is one way or is a round trip',
                            reply_markup=reply_markup)
    return ONEWAY_ROUNDTRIP

async def set_oneway_or_roundtrip_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global oneway_or_roundtrip_option

    user_option = ''
    valid_answers = ['one way', 'round trip']
    while user_option not in valid_answers:
        user_option = update.message.text.lower()
        if user_option in valid_answers:
            break

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text=f"The search option {user_option} is not valid.\nPlease use buttons to answer") 
        update = await context.bot.get_updates(update_id=update.update_id+1)  

    if user_option == 'round trip':
        oneway_or_roundtrip_option = False
    elif user_option == 'one way':
        oneway_or_roundtrip_option = True  

    await context.bot.send_message(chat_id=update.effective_chat.id,
                            text="Enter the departure date in the format YYYY-MM-DD",
                            reply_markup=ReplyKeyboardRemove())
    return DEPARTURE_DATE


async def set_departure_date(update, context):
    global departure_date
    verification = False
    while not verification:
        departure_date = update.message.text
        verification = is_valid_date(departure_date)
        if verification:
            print(f'The departure date is valid')
            break
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text=f"The departure date {departure_date} is not valid.\nPlease type the correct departure date in the format YYYY-MM-DD") 
        update = await context.bot.get_updates(update_id=update.update_id+1)
    if not oneway_or_roundtrip_option:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Provide the date when you are coming back in the format YYYY-MM-DD")
        return DESTINATION_DATE 
       
    else:
        exact_start_date = departure_date
        exact_finish_date = ''
        flight_offers = get_flight_offers(departure_city_code, destination_city_code, exact_start_date, exact_finish_date, oneway_or_roundtrip_option)
        if not flight_offers:
            # handle the case when data_list is empty
            error_message = "Sorry, we couldn't find any flights for your search parameters. Please try again with different parameters."
            update.message.reply_text(error_message)
            return
        good_looking_flight_offers = send_flight_offers(flight_offers)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Searching for the flights on {departure_date}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=good_looking_flight_offers)
        return ConversationHandler.END
    
async def set_destination_date(update, context):
    global destination_date

    verification = False
    while not verification:
        destination_date = update.message.text
        verification = is_valid_date(destination_date)
        if verification:
            print(f'The destination date is valid')
            break
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text=f"The destination date {destination_date} is not valid.\nPlease type the correct destination date in the format YYYY-MM-DD") 
        update = await context.bot.get_updates(update_id=update.update_id+1)       
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Searching for the flights on every weekend starting from {departure_date} to {destination_date}")

    if not oneway_or_roundtrip_option:
        saturdays = calendar(SA)
        sundays = calendar(SU)      
        for x in range(len(sundays)):
            exact_start_date = saturdays[x]
            exact_finish_date = sundays[x]
            flight_offers = get_flight_offers(departure_city_code, destination_city_code, exact_start_date, exact_finish_date, oneway_or_roundtrip_option)
            if not flight_offers:
                # handle the case when data_list is empty
                error_message = "Sorry, we couldn't find any flights for your search parameters. Please try again with different parameters."
                update.message.reply_text(error_message)
                return

            good_looking_flight_offers = send_flight_offers(flight_offers)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=good_looking_flight_offers)

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Searching is finished")
    return ConversationHandler.END

async def cancel(update, context):
    """Cancels the conversation and sends a message to the user."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("Ok, let's abort the search")
    return ConversationHandler.END

async def skip_destination_city(update, context):
    global destination_city_code
    destination_city_code = ''
    user = update.message.from_user
    logger.info("User %s did not send a destination city.", user.first_name)

    reply_keyboard = [['One way', 'Round trip']]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True, selective=True, input_field_placeholder='Choose weather the flight is one way or a round trip')
    await context.bot.send_message(chat_id=update.effective_chat.id,
                            text="The destination city is not set. Choose weather the flight is one way or a round trip",
                            reply_markup=reply_markup)
    return ONEWAY_ROUNDTRIP

# Define main function
def main()-> None:
    
    # Create the application instance
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
  
    conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_currency)],
        DEPARTURE_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_departure_city)],
        DESTINATION_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_destination_city),
                           CommandHandler("skip", skip_destination_city),
                           ],
        ONEWAY_ROUNDTRIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_oneway_or_roundtrip_option)],
        DEPARTURE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_departure_date)],
        DESTINATION_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_destination_date)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add conversation handler to application
    application.add_handler(conv_handler)


    # Start the application
    application.run_polling()
    
if __name__ == '__main__':
    main()


    """comment"""

    
    """comment2"""