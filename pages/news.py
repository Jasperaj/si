import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd



def fetch_sharesansar_news():
    url = 'https://sharesansar.com/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    news_section = soup.find('div', class_='news-section')
    news_items = news_section.find_all('a', class_='news-title')
    news = [{'title': item.text.strip(), 'link': item['href']} for item in news_items]
    return news

def fetch_merolagani_news():
    url = 'https://merolagani.com/NewsList.aspx'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    news_section = soup.find('div', class_='news-list')
    news_items = news_section.find_all('a', class_='news-title')
    news = [{'title': item.text.strip(), 'link': 'https://merolagani.com/' + item['href']} for item in news_items]
    return news

def fetch_nepsealpha_news():
    url = 'https://nepsealpha.com/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    news_section = soup.find('div', class_='news-section')
    news_items = news_section.find_all('a', class_='news-title')
    news = [{'title': item.text.strip(), 'link': 'https://nepsealpha.com/' + item['href']} for item in news_items]
    return news




def fetch_nepse_index_summary():
    url = 'https://nepalstock.com.np/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    index_summary = soup.find('div', class_='index-summary')
    index_value = index_summary.find('span', class_='index-value').text.strip()
    change_value = index_summary.find('span', class_='change-value').text.strip()
    return {'index_value': index_value, 'change_value': change_value}


def news_main():
    st.title("Nepal Stock Market News and Index Summary")

    st.header("NEPSE Index Summary")
    index_summary = fetch_nepse_index_summary()
    st.write(f"**Index Value:** {index_summary['index_value']}")
    st.write(f"**Change:** {index_summary['change_value']}")

    st.header("Latest News")

    st.subheader("ShareSansar")
    sharesansar_news = fetch_sharesansar_news()
    for news in sharesansar_news:
        st.write(f"- [{news['title']}]({news['link']})")

    st.subheader("MeroLagani")
    merolagani_news = fetch_merolagani_news()
    for news in merolagani_news:
        st.write(f"- [{news['title']}]({news['link']})")

    st.subheader("NepseAlpha")
    nepsealpha_news = fetch_nepsealpha_news()
    for news in nepsealpha_news:
        st.write(f"- [{news['title']}]({news['link']})")

if __name__ == "__main__":
    news_main()



