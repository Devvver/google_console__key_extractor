import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import date

# Настройка ширины страницы
st.set_page_config(page_title="Google Search Console Exporter", layout="wide")

# Настройка Streamlit
st.title("Google Search Console Data Exporter")
st.markdown("Введите домен, выберите диапазон дат и получите данные в формате CSV.")

# Пользовательский ввод
domain = st.text_input("Введите домен сайта с https:// (например, https://example.com):", "")
start_date = st.date_input("Дата начала:", value=date(2024, 1, 1))
end_date = st.date_input("Дата окончания:", value=date.today())
export_button = st.button("Получить данные")

# Функция для получения всех данных через Google Search Console API
def get_all_search_console_data(site_url, start_date, end_date):
    credentials_path = "credentials.json"  # Укажите путь к вашему credentials.json
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
    )

    service = build("searchconsole", "v1", credentials=credentials)
    all_results = []
    start_row = 0
    row_limit = 1000

    progress_bar = st.progress(0)
    progress_text = st.empty()
    current_step = 0

    while True:
        request = {
            "startDate": str(start_date),
            "endDate": str(end_date),
            "dimensions": ["query", "page"],
            "rowLimit": row_limit,
            "startRow": start_row
        }

        response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
        rows = response.get("rows", [])
        if not rows:
            break

        for row in rows:
            query = row["keys"][0]
            url = row["keys"][1] if len(row["keys"]) > 1 else "N/A"
            clicks = row.get("clicks", 0)
            impressions = row.get("impressions", 0)
            position = row.get("position", 0)  # Получаем позицию
            all_results.append({
                "Ключевой запрос": query,
                "URL": url,
                "Клики": clicks,
                "Показы": impressions,
                "Позиция": position
            })

        current_step += 1
        progress_text.text(f"Запросов выполнено: {current_step * row_limit}")
        progress_bar.progress(min(current_step * row_limit / 10000, 1.0))

        start_row += row_limit

    progress_bar.empty()
    progress_text.empty()

    return all_results

if export_button and domain:
    try:
        st.info("Получение всех данных...")
        data = get_all_search_console_data(domain, start_date, end_date)
        if data:
            df = pd.DataFrame(data)
            st.success(f"Данные успешно получены! Всего строк: {len(df)}")
        else:
            df = pd.DataFrame()
            st.warning("Нет данных для отображения.")

    except Exception as e:
        st.error(f"Ошибка: {e}")
        if "df" not in locals():
            df = pd.DataFrame()

    st.dataframe(df)

    if not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Экспортировать в CSV",
            data=csv,
            file_name="search_console_data.csv",
            mime="text/csv",
        )
