import openai
import json
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.options import Options
from urllib.parse import quote
from common.helpers import get_prompt
from config.env import OPENAI_API_KEY
from config.prompts import EXTRACT_KEYWORDS_PROMPT


def get_browser(show_browser: bool = False) -> ChromiumDriver:
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    if not show_browser:
        chrome_options.add_argument('--headless')

    return webdriver.Chrome(options=chrome_options)


def get_product_description(browser: ChromiumDriver, product_url: str) -> str:
    browser.get(product_url)
    wait = WebDriverWait(browser, 10)

    description_button = wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "button.product-page__btn-detail.hide-mobile.j-details-btn-desktop")))
    description_button.click()

    description_element = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "section.product-details__description.option")))
    description = description_element.find_element(By.CSS_SELECTOR, "p.option__text").text

    return description


def find_product_positions(browser: ChromiumDriver, keywords: list[str], product_url: str) -> list[dict]:
    result_positions = []
    original_product_id = product_url.split('/')[-2]
    
    for keyword in keywords:
        try:
            search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={quote(keyword)}"
            browser.get(search_url)

            wait = WebDriverWait(browser, 10)
            wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "a.product-card__link")))

            product_cards = browser.find_elements(By.CSS_SELECTOR, "a.product-card__link")
            result_position = 0

            for position, card in enumerate(product_cards, 1):
                try:
                    if str(original_product_id) in card.get_attribute("href"):
                        result_position = position + 1
                        break
                except (Exception,):
                    continue

            result_positions.append({
                'keyword': keyword,
                'position': result_position
            })

        except Exception as e:
            print(f"Ошибка при поиске по ключевой фразе '{keyword}': {e}")
            continue

    return result_positions


def extract_keywords_from_description(
        product_description: str,
        keywords_count: int
) -> list[str]:
    try:
        prompt = get_prompt(
            prompt=EXTRACT_KEYWORDS_PROMPT,
            product_description=product_description,
            keywords_count=keywords_count
        )

        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            temperature=0.7,
            max_tokens=150,
            api_key=OPENAI_API_KEY
        )

        phrases = json.loads(response.choices[0].text.strip())
        
        return phrases
    
    except Exception as e:
        print(f"Ошибка при работе с OpenAI: {e}")
        return []


def find_relevant_positions(
        product_url: str,
        keywords_count: int,
        show_browser: bool = False
):
    browser = get_browser(show_browser=show_browser)

    description = get_product_description(browser, product_url)
    keywords = extract_keywords_from_description(description, keywords_count)
    positions = find_product_position(browser, keywords, product_url)

    browser.quit()

    return {
        'product_url': product_url,
        'description': description,
        'keywords': keywords,
        'positions': positions
    }


if __name__ == "__main__":
    result = find_relevant_positions(
        product_url=input('Введите URL товара WB: '),
        keywords_count=5,
        show_browser=True
    )
    pprint(result)
