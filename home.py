import cv2
import numpy as np
import pandas as pd
import streamlit as st

from bot.scheme.enums import Currency, ShippingType
from bot.services.gpt import TextQuoteParserGPT
from bot.workers import pdf, quote

st.title("DExpress: автоматизация")


tab_quote, tab_orders = st.tabs(["Проценки", "Заказы"])


def _render_dataframe(table: pd.DataFrame, default_columns: list[str]):
    cols = list(table.columns)
    selected_cols = st.multiselect(
        label="Показать столбцы", options=cols, default=default_columns
    )
    st.dataframe(table[selected_cols])


@st.cache_data
def _parse_quote(src: str | bytes) -> pd.DataFrame:
    if isinstance(src, str):
        quote_parser = quote.QuoteParserText(
            src=quote_text, text_parser=TextQuoteParserGPT()
        )
    else:
        quote_parser = quote.QuoteParserScreenshot(
            src=src, text_parser=TextQuoteParserGPT()
        )
    tbl = quote_parser.run(weight=True)
    return quote_parser, tbl


@st.cache_data
def _convert_currency(
    parser: quote.QuoteParserText,
    results: pd.DataFrame,
    from_currency: Currency,
    to_currency: Currency,
) -> pd.Series:
    return parser.convert_currency(results, from_currency, to_currency)


def _parse_quote_total(
    src: str | bytes,
    vat: float = 0.05,
    shipping_type: ShippingType = ShippingType.air,
    to_currency: Currency = Currency.rub,
) -> pd.DataFrame:
    quote_parser, res = _parse_quote(src)
    tbl = quote_parser.as_table(res)
    if len(tbl) > 0:
        shipping_col = f"shipping_{shipping_type.value}"
        tbl["total"] = quote_parser.calculate_unit_total(
            tbl, vat=vat, shipping=shipping_col
        )
        tbl[to_currency.value] = _convert_currency(
            quote_parser, tbl, Currency.aed, to_currency
        )
    return tbl


@st.cache_data
def _process_pdf_order(vendor_name: str, pdf_order) -> pd.DataFrame:
    pdf_proc = suppliers[vendor_name](pdf_order)
    return pdf_proc.run()


with st.sidebar:
    vat = st.number_input(label="НДС", min_value=0.0, max_value=1.0, value=0.05)
    shipping_type = st.radio("Тип доставки", [ShippingType.air, ShippingType.container])
    currency = st.selectbox(
        label="Валюта",
        options=[Currency.rub, Currency.aed, Currency.eur, Currency.usd],
        format_func=lambda x: x.value,
    )

with tab_quote:
    quote_text = st.text_area(label="Вставьте текст проценки")
    quote_screenshot = st.file_uploader(label="Загрузите скриншот")

    default_columns = [
        "part_number",
        "price",
        "lead_time_days",
        "weight",
        "shipping_air",
        "shipping_container",
    ]

    if quote_text:
        with st.spinner("Обработка текста"):
            out = _parse_quote_total(quote_text, vat=vat, shipping_type=shipping_type)
            if out:
                _render_dataframe(out, default_columns=default_columns)
            else:
                st.error("Не удалось распознать текст")

    elif quote_screenshot:
        a = np.frombuffer(
            quote_screenshot.read(), dtype=np.uint8
        )  # pylint: disable=no-member
        a = cv2.imdecode(a, cv2.IMREAD_COLOR)  # pylint: disable=no-member
        st.image(a, channels="RGB")

        with st.spinner("Обработка изображения"):
            res = _parse_quote_total(a, vat=vat, shipping_type=shipping_type)
            if len(res) > 0:
                _render_dataframe(res, default_columns=default_columns)
            else:
                st.error("Не удалось распознать текст")

with tab_orders:
    suppliers = {
        "European Autospares": pdf.PdfOrderEuropeanAutospares,
        "Humaid Ali": pdf.PdfOrderHumaidAli,
        "HND": pdf.PdfOrderHND,
    }
    vendor_name = st.selectbox(label="Поставщик", options=list(suppliers.keys()))
    pdf_order = st.file_uploader("Загрузи пдф файл с заказом")

    if pdf_order:
        res = _process_pdf_order(vendor_name, pdf_order)

        _render_dataframe(
            res,
            default_columns=[
                "invoice_date",
                "supplier_name",
                "part_number",
                "quantity",
                "price",
            ],
        )
