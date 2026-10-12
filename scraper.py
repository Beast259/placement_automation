import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime
import os

def scrape_emails_from_url(url):
    """
    Scrape email addresses from a given URL.
    Returns a list of unique email addresses found.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all text and look for email patterns
    text = soup.get_text()
    # Regex for email addresses
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    
    # Also look for mailto links
    mailto_links = soup.find_all('a', href=True)
    for link in mailto_links:
        href = link['href']
        if href.startswith('mailto:'):
            email = href[7:]  # Remove 'mailto:'
            # Sometimes there are parameters after ? in mailto
            email = email.split('?')[0]
            if re.match(email_pattern, email):
                emails.append(email)
    
    # Remove duplicates and return
    return list(set(emails))

def scrape_company_list(urls_file):
    """
    Read a list of URLs from a file and scrape emails from each.
    Returns a list of dictionaries with company info and emails.
    """
    results = []
    try:
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"URLs file {urls_file} not found.")
        return results

    for url in urls:
        print(f"Scraping {url}...")
        emails = scrape_emails_from_url(url)
        if emails:
            # We'll use the URL as company identifier for now
            # In a real scenario, we might extract company name from the page
            company_name = extract_company_name(url, BeautifulSoup(requests.get(url).text, 'html.parser') if 'requests' in locals() else None)
            for email in emails:
                results.append({
                    'company_name': company_name,
                    'email': email,
                    'source_url': url,
                    'date_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        else:
            print(f"No emails found at {url}")
    
    return results

def extract_company_name(url, soup=None):
    """
    Attempt to extract company name from URL or page.
    This is a simple implementation - can be improved.
    """
    # If we have soup, try to get title or specific meta tags
    if soup:
        # Try to get from title tag
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
            # Clean up title - remove common suffixes
            title = re.sub(r'\s*[-–]\s*.*$', '', title)  # Remove everything after dash
            if title:
                return title
        
        # Try to get from meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            if tag.get('property') == 'og:site_name' or tag.get('name') == 'application-name':
                content = tag.get('content')
                if content:
                    return content.strip()
    
    # Fallback: extract domain from URL
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        # Remove common TLDs and take the main part
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            # Assume the second last part is the main domain (e.g., example in example.com)
            return domain_parts[-2].replace('-', ' ').title()
    except:
        pass
    
    return url  # Return URL as last resort

def save_to_csv(data, filename='companies.csv'):
    """
    Save scraped data to a CSV file.
    """
    if not data:
        print("No data to save.")
        return
    
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['company_name', 'email', 'source_url', 'date_scraped']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for row in data:
            writer.writerow(row)
    
    print(f"Saved {len(data)} records to {filename}")

if __name__ == "__main__":
    # Example usage: scrape from a file containing URLs
    urls_file = 'urls.txt'  # Create this file with one URL per line
    data = scrape_company_list(urls_file)
    save_to_csv(data)