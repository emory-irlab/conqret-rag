import requests
from bs4 import BeautifulSoup
import json
import utils
import glob

test_files = glob.glob(utils.PROCON_TEST_FOLDER)
TEST_FILE_NAMES = [f.split('/')[-1] for f in test_files]

def get_html_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None


def get_title(soup):
    try:
        title = soup.find('h1', class_='entry-title')
        if title:
            title = title.get_text(strip=True)
            return title
        else:
            title = soup.find('h1',class_='text-center')
            if title:
                title = title.get_text(strip=True)
            else:
                # If no h1 title, look for a meaningful title in image alt attributes
                image = soup.find('div', {'class': 'topic-question-image-wrapper'})
                if image and 'alt' in image.attrs:
                    alt_text = image['alt'].strip()
                    if len(alt_text) > 10:  # Ensuring the alt text is lengthy enough to be a title
                        title = alt_text
            return title
    except Exception as e:
        print(f"Error extracting title: {e}")
        return None

def get_titles(soup):
    titles = []
    try:
        # If no <title> tag, look specifically for <h3> tags with the exact class and style
        header_tag = soup.find('h3', {"class": "boxed-blue", "style": "margin-top:1rem"})
        if header_tag:
            titles.append(header_tag.text)
        title_tag = soup.find('title')
        if title_tag:
            titles.append(title_tag.get_text(strip=True))
        title = soup.find('h1', class_='entry-title')
        if title:
            title = title.get_text(strip=True)
            titles.append( title)
        title = soup.find('h1',class_='text-center')
        if title:
            title = title.get_text(strip=True)
            titles.append(title)
        else:
            # If no h1 title, look for a meaningful title in image alt attributes
            image = soup.find('div', {'class': 'topic-question-image-wrapper'})
            if image and 'alt' in image.attrs:
                alt_text = image['alt'].strip()
                if len(alt_text) > 10:  # Ensuring the alt text is lengthy enough to be a title
                    title = alt_text
                    titles.append(title)
    except Exception as e:
        print(f"Error extracting title: {e}")
    return titles


def extract_filename_from_url(url):
    if url.endswith('/'):
        url = url[:-1]
    return url.split('/')[-1] + '.json'


def get_citations_from_table(table, docid):
    citations = []
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 3:
            cid = cols[1].get_text(strip=True).strip('.')
            if not cid:
                cid = cols[1].find('a')['name']
            title = cols[2].get_text(strip=True)
            url = cols[2].find('a')['href'] if cols[2].find('a') else None
            citations.append({'id': cid, 'title': title, 'url': url, 'docid': docid})
            docid +=1
        elif len(cols) == 2:
            cid = cols[0].get_text(strip=True).strip('.')
            title = cols[1].get_text(strip=True)
            citations.append({'id': cid, 'title': title, 'docid': docid})
            docid +=1
    return citations, docid

def parse_html_to_json(html_content, filename, url, docid):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract the title
    #title_main = get_title(soup)
    # if not title_main:
    #     title_main = filename

    titles = get_titles(soup)
    titles.append(filename)
    # Extract all <p> tags in the introduction section
    intro_ps = [p.get_text(strip=True) for p in soup.find('div', class_='entry-content').find_all('p', recursive=False)]

    # Extract pros
    pros = []
    pros_container = soup.find('div', class_='arguments-column-pro')
    if pros_container:
        pros_blocks = pros_container.find_all('div', class_='argument-container')
        for block in pros_blocks:
            title = block.find('h4').get_text(strip=True)
            text_paragraphs = [p.get_text(strip=True) for p in block.find_all('p')]
            pros.append({'title': title, 'paragraphs' : text_paragraphs})

    # Extract cons
    cons = []
    cons_container = soup.find('div', class_='arguments-column-con')
    if cons_container:
        cons_blocks = cons_container.find_all('div', class_='argument-container')
        for block in cons_blocks:
            title = block.find('h4').get_text(strip=True)
            text_paragraphs = [p.get_text(strip=True) for p in block.find_all('p')]
            cons.append({'title': title, 'paragraphs' : text_paragraphs})

    citations = []
    table=None
    source_sections = [p for p in soup.find('div', class_='entry-content').find_all('p', recursive=False) if p.get_text(strip=True)=='Sources']
    if source_sections and len(source_sections)>0:
        table = source_sections[0].find_next('table')
    elif soup.find('table', class_='tablepress') and not soup.find('table', class_='tablepress').get_text().strip().startswith('Did You'):
        table = soup.find('table', class_='tablepress')
    else:
        footnotes_html = get_html_content(url + '/footnotes/')
        if footnotes_html:
            footnotes_soup = BeautifulSoup(footnotes_html, 'html.parser')
            table = footnotes_soup.find('table')
    if table:
        citations, docid = get_citations_from_table(table, docid)

    data = {
        #'title': title_main,
        'titles': titles,
        'introduction': intro_ps,
        'pros': pros,
        'cons': cons,
        'sources': citations
    }

    if "Discussion Questions" in intro_ps:
        discussion_index = intro_ps.index("Discussion Questions")
        introduction = intro_ps[:discussion_index]
        data['introduction'] = introduction
        data['discussion'] = intro_ps[discussion_index + 1:]
        if "Take Action" in intro_ps:
            action_index = intro_ps.index("Take Action")
            data['introduction'] = introduction
            discussion = intro_ps[discussion_index + 1:action_index]
            data['discussion'] = discussion
            data['action'] = intro_ps[action_index + 1:]
            if "Sources" in intro_ps:
                sources_index = intro_ps.index("Sources")
                action = intro_ps[action_index + 1:sources_index]
                data['action'] = action
                #data['sources'] = intro_ps[sources_index + 1:]
    # Split the list into the three parts
    # Create JSON structure
    return data, docid, titles

"""
Goes through the ProCon.prg website's URLs and then parses them.
URLs from Procon.org --> HTML parse --> JSON --> ../procon
"""
if __name__ == '__main__':
    DOCID = 0
    url2titles = {}
    qid = 0
    with open(f'url_list.txt','r+') as ufile:
        urls = ufile.readlines()
        urls = [url.strip() for url in urls]
        urls = set(urls)
        grounded = 0
        total_citations = 0
        pros = 0
        cons = 0
        for url in urls:
            print(f"URL {url}")
            html_content = get_html_content(url)
            if html_content:
                json_filename = extract_filename_from_url(url)
                print(f"Extracting from filename: {json_filename}")
                try:
                    data, DOCID, titles = parse_html_to_json(html_content, json_filename, url, DOCID)
                    url2titles[url] = {'titles': titles, 'qid' : qid}
                    qid += 1
                    # Save to JSON file
                    data['url'] = url
                    # count
                    grounded += int(len(data['sources']) > 0)
                    pros += len(data['pros'])
                    cons += len(data['cons'])
                    #json_filename = data['title'].replace(' ','_').replace('-','_').replace('--','').replace('?','') + '.json'
                    json_filename = data['titles'][0].replace(' ', '_').replace('-', '_').replace('--', '').replace('?', '') + '.json'
                    saveto = 'test/' if json_filename in TEST_FILE_NAMES else 'train/'
                    with open(f'procon/{saveto}{json_filename}', 'w') as json_file1:
                       json.dump(data, json_file1, indent=4)
                    print(f"Data saved to {json_filename}")
                except Exception as e:
                    print(e)
                    print(f'Exception while parsing')
        print(f'The number of procon debates grounded in citations are {grounded}.\nTotal citations are {DOCID}.\nA total of {pros} pro arguments and {cons} arguments.')
        with open(f'titles1.json','w+') as tfile:
            json.dump(url2titles, tfile, indent=4)
            print(f"Titles saved to titles.json")
