import tempfile

import streamlit as st

from bot.workers import pdf, quote, text

st.title("DExpress: автоматизация")


tab_quote, tab_orders = st.tabs(["Проценки", "Заказы"])


with tab_quote:
    quote_text = st.text_area(label="Вставьте текст проценки")
    quote_screenshot = st.file_uploader(label="Загрузите скриншот")

    if quote_text:
        parser_text = quote.QuoteParserText(
            src=quote_text, text_parser=text.TextQuoteParserRegex()
        )
        out = parser_text.run()
        st.table(parser_text.as_table(out))

    if quote_screenshot:
        # parser_shot = quote.QuoteParserScreenshot(src=quote_screenshot,
        # parser_shot.run()
        # TODO read and process file
        pass

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

        cols = list(res.columns)
        selected_cols = st.multiselect(
            label="Выбрать столбцы",
            options=cols,
            default=[
                "invoice_date",
                "supplier_name",
                "part_number",
                "quantity",
                "price",
            ],
        )
        st.dataframe(res[selected_cols])
