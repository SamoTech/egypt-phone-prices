import requests
from bs4 import BeautifulSoup
import re

print("🔍 Testing Jumia Egypt...")
url = "https://www.jumia.com.eg/mlp/electronics/phones/"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    response
