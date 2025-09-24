import httpx
import asyncio
from bs4 import BeautifulSoup
import pandas as pd


# --- НАСТРОЙКИ ---
# Заполните базовый URL для парсинга и колличество страниц

BASE_URL = "https://career.habr.com/companies"
QUERY_PARAM = "?page="
COUNT_URLS = 5

# Укажите CSS-селекторы (классы) для данных, которые хотите собрать.
COMPANY_BLOCK_SELECTOR = "div.companies-item-name"
NAME_SELECTOR = "a"

async def fetch_page(client, url):
    """Асинхронно загружает одну страницу и возвращает ее HTML-содержимое."""
    
    try:
        # Добавляем заголовок User-Agent, чтобы имитировать обычный браузер
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = await client.get(url, headers=headers, follow_redirects=True, timeout=15)
        response.raise_for_status()  # Проверка на ошибки (4xx или 5xx)
        return response.text
    except httpx.HTTPStatusError as e:
        print(f"Ошибка HTTP при доступе к {url}: {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"Ошибка запроса к {url}: {e}")
    return None


def parse_html(html_content):
    """Извлекает данные из HTML-кода одной страницы."""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    company_blocks = soup.select(COMPANY_BLOCK_SELECTOR)
    page_results = []

    for block in company_blocks:
        name_tag = block.select_one(NAME_SELECTOR)
        name = name_tag.text.strip() if name_tag else "Название не найдено"
        link = name_tag.get('href')

        page_results.append({
            'Название компании': name,
            'Ссылка': link
        })
    return page_results


async def main():
    """Основная функция: запускает загрузку и парсинг, сохраняет результат."""
    
    print("Запуск асинхронного парсера...")
    all_results = []
    
    async with httpx.AsyncClient() as client:
        # Создаем список задач для одновременного выполнения
        tasks = [fetch_page(client, f"{BASE_URL}{QUERY_PARAM}{num}") for num in range(1, COUNT_URLS + 1)]
        # Запускаем все задачи и ждем их завершения
        html_pages = await asyncio.gather(*tasks)

    for html in html_pages:
        if html:
            all_results.extend(parse_html(html))
    
    # Сохранение в CSV
    if not all_results:
        print("Не удалось собрать данные. Проверьте CSS-селекторы и URL-адреса.")
        return

    df = pd.DataFrame(all_results)
    df = df.drop_duplicates().reset_index(drop=True)  # Удаляем дубликаты
    
    # Имя файла для сохранения
    output_filename = 'clients_base.csv'
    df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    
    print(f"\nГотово! Собрано {len(df)} уникальных контактов.")
    print(f"Результаты сохранены в файл: {output_filename}")


if __name__ == "__main__":
    asyncio.run(main())
