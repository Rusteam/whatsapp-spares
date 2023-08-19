import streamlit as st

from bot.workers import quote, text

st.title("DExpress: автоматизация")


tab_quote_text, tab_quote_screenshot = st.tabs(
    ["Проценки: текст", "Проценки: скриншот"]
)


with tab_quote_text:
    quote_text = st.text_area(label="Вставьте текст проценки")

    if quote_text:
        parser_text = quote.QuoteParserText(
            src=quote_text, text_parser=text.TextQuoteParserRegex()
        )
        out = parser_text.run()
        st.table(parser_text.as_table(out))

with tab_quote_screenshot:
    quote_screenshot = st.file_uploader(label="Загрузите скриншот")

    if quote_screenshot:
        # parser_shot = quote.QuoteParserScreenshot(src=quote_screenshot,
        # parser_shot.run()
        # TODO read and process file
        pass
