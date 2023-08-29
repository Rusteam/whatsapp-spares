import cv2
import numpy as np
import pandas as pd
import streamlit as st

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


with tab_quote:
    quote_text = st.text_area(label="Вставьте текст проценки")
    quote_screenshot = st.file_uploader(label="Загрузите скриншот")
    default_columns = ["part_number", "price", "lead_time_days"]

    if quote_text:
        with st.spinner():
            # TODO cache results
            parser_text = quote.QuoteParserText(
                src=quote_text, text_parser=TextQuoteParserGPT()
            )
            out = parser_text.run(weight=True)
            if out:
                _render_dataframe(
                    parser_text.as_table(out), default_columns=default_columns
                )
            else:
                st.error("Не удалось распознать текст")

    elif quote_screenshot:
        a = np.frombuffer(
            quote_screenshot.read(), dtype=np.uint8
        )  # pylint: disable=no-member
        a = cv2.imdecode(a, cv2.IMREAD_COLOR)  # pylint: disable=no-member
        st.image(a, channels="RGB")

        with st.spinner():
            parser = quote.QuoteParserScreenshot(
                src=a, text_parser=TextQuoteParserGPT()
            )
            res = parser.run()
            res = parser.as_table(res)
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
        pdf_proc = suppliers[vendor_name](pdf_order)
        res = pdf_proc.run()

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
