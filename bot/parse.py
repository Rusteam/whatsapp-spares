"""Parse input messages and format them for the output.
"""
import re
from datetime import datetime as dt

from bot.scheme import InputMessage, OutputMessage, Constants
from bot.services import get_exchange_rate

CONSTANTS = Constants()


def _parse_part_number(message):
    """Parse the part number from the message.
    """
    PART_NUM_PATTERN = r"(A\d+)"
    part_num_match = re.match(PART_NUM_PATTERN, message, flags=re.IGNORECASE)
    part_num = part_num_match.group(1) if part_num_match else None
    if part_num:
        message = re.sub(f"{part_num}( \- )?", "", message)
        part_num = part_num.upper()
    return part_num, message.strip()


def _parse_price(message):
    """Parse the price from the message.
    """
    PRICE_PATTERN = r"(\d+)\s+(\+\s+vat)"
    price_match = re.match(PRICE_PATTERN, message, flags=re.IGNORECASE)
    if price_match:
        price = float(price_match.group(1))
        vat = False if "no vat" in message else True
        message = re.sub(PRICE_PATTERN, "", message)
    else:
        price = 0
        vat = True
    return price, vat, message.strip()


def _parse_lead_time(message):
    """Parse the lead time from the message.
    """
    LEAD_TIME_PATTERN = r"(\d+|\d+\-\d+) (day|week|month)s?"
    lead_time_match = re.match(LEAD_TIME_PATTERN, message, flags=re.IGNORECASE)
    if lead_time_match:
        num = lead_time_match.group(1)
        if "-" in num:
            num = max(list(map(int, num.split("-"))))
        else:
            num = int(num)

        period = lead_time_match.group(2)
        match period:
            case "day":
                lead_days = num
            case "week":
                lead_days = num * 7
            case "month":
                lead_days = num * 30
            case _:
                raise ValueError(f"Unknown lead time period: {period}")

        message = re.sub(LEAD_TIME_PATTERN, "", message)
    elif "back order" in message or "no eta" in message:
        lead_days = CONSTANTS.back_order_lead_days
        message = re.sub(r"(back order|no eta)", "", message)
    else:
        lead_days = 0
    return lead_days, message.strip()


def parse_input_message(message) -> list[InputMessage]:
    lines = message.splitlines()
    return [parse_input_line(line) for line in lines]


def parse_input_line(message) -> InputMessage:
    """Parse the message and return the output message.
    """
    message = message.strip().lower()

    try:
        part_num, message = _parse_part_number(message)
    except Exception as e:
        print("Error parsing part number: ", e)
        part_num = None

    try:
        price, vat, message = _parse_price(message)
    except Exception as e:
        print("Error parsing price: ", e)
        price = 0
        vat = True

    try:
        lead_days, message = _parse_lead_time(message)
    except Exception as e:
        print("Error parsing lead time: ", e)
        lead_days = 0

    return InputMessage(price=price, lead_days=lead_days, part_number=part_num, vat=vat)


def calc_selling_price(price, ex_rate):
    direct_cost = price * (1 + CONSTANTS.vat) * ex_rate
    extra_cost = direct_cost * (CONSTANTS.profit_margin + CONSTANTS.currency_conversion_charge)
    total_cost = direct_cost + extra_cost
    return total_cost


def prepare_output(message: InputMessage) -> OutputMessage:
    """Convert the message to the output format.
    """
    today_str = _get_today()
    ex_rate = get_exchange_rate(message.currency, "RUB", today_str)
    total_cost = calc_selling_price(message.price, ex_rate)
    return OutputMessage(price=total_cost,
                         lead_days=message.lead_days + CONSTANTS.shipping_days,
                         part_number=message.part_number)


def _get_today() -> str:
    return dt.today().strftime("%Y-%m-%d")


def process_message(message: str) -> OutputMessage:
    """Process the message and return the output message.
    """
    input_message = parse_input_message(message)
    return [prepare_output(msg) for msg in input_message]


if __name__ == '__main__':
    today = _get_today()
    rate = get_exchange_rate("AED", "RUB", today)
    print(f"{today=} {rate=:.1f} from AED to RUB")
