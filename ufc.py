import requests as req
from lxml import html
import datetime as dt
import math
import re

def parse_sherdog_fighter(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"}
    htm = req.get(url, headers = headers)
    xml = html.document_fromstring(htm.content)
    
    
    wins_detailed = xml.xpath("//div[@class='wins']/div[@class='meter']/div[1]/text()")
    losses_detailed = xml.xpath("//div[@class='loses']/div[@class='meter']/div[1]/text()")
    bio = xml.xpath("//div[@class='fighter-info']")[0]
    
    try:
        other_wins = wins_detailed[3]
        other_losses = losses_detailed[3]
    except IndexError:
        other_wins = '0'
        other_losses = '0'

    fighter = {
        'name' : xml.xpath("//span[@class='fn']/text()")[0],
        'nickname' : bio.xpath("//span[@class='nickname']/em/text()")[0],
        'nationality' : bio.xpath("//strong[@itemprop='nationality']/text()")[0],
        'birthplace' : xml.xpath("//span[@class='locality']/text()")[0],
        'birthdate' : xml.xpath("//span[@itemprop='birthDate']/text()")[0],
        'age' : xml.xpath("//span[@itemprop='birthDate']/preceding-sibling::b/text()")[0],
        'height' : xml.xpath("//b[@itemprop='height']/text()")[0],
        'weight' : xml.xpath("//b[@itemprop='weight']/text()")[0],
        'association' : xml.xpath("//span[@itemprop='memberOf']/a/span/text()")[0],
        'weight_class' : xml.xpath("//div[@class='association-class']/a/text()")[0],

        'wins' : {
            'total': xml.xpath("//div[@class='winloses win']/span[2]/text()")[0],
            'ko/tko': wins_detailed[0],
            'submissions':wins_detailed[1],
            'decisions':wins_detailed[2],
            'others': other_wins
                },
        'losses' : {
            'total': xml.xpath("//div[@class='winloses lose']/span[2]/text()")[0],
            'ko/tko': losses_detailed[0],
            'submissions':losses_detailed[1],
            'decisions':losses_detailed[2],
            'others':other_losses
                },

        'fights' : []
    }

    fight_rows = xml.xpath("//table[@class='new_table fighter']/tr[not(@class='table_head')]")

    for row in fight_rows:
        try:
            referee =  row.xpath("td[4]/span/a/text()")[0]
        except IndexError:
            referee = ""

        fight = {
            'name': row.xpath("td[3]/a/descendant-or-self::*/text()")[0],
            'date': row.xpath("td[3]/span/text()")[0],
            'url': "https://www.sherdog.com" + row.xpath("td[3]/a/@href")[0],
            'result': row.xpath("td[1]/span/text()")[0],
            'method': row.xpath("td[4]/b/text()")[0],
            'referee': referee,
            'round': row.xpath("td[5]/text()")[0],
            'time': row.xpath("td[6]/text()")[0],
            'opponent': row.xpath("td[2]/a/text()")[0]
        }
        fighter['fights'].append(fight)
    return fighter

def get_ufc_stats(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"}
    htm = req.get(url, headers = headers)
    xml = html.document_fromstring(htm.content)

    str_tds = xml.xpath("//dd/text()")
    distance = xml.xpath("//div[@class='c-stat-3bar__value']/text()")
    stats = xml.xpath("//div[@class='c-stat-compare__number']/text()")

    fighter = {
        'strikes': {
            'attempted': str_tds[1],
            'landed': str_tds[0],
            'standing': distance[0].split(" ")[0],
            'clinch': distance[1].split(" ")[0],
            'ground': distance[2].split(" ")[0],
            'striking defense': stats[4].strip(),
            'strikes per minute': stats[0].strip()
        },
        'takedowns': {
            'attempted': str_tds[3],
            'landed': str_tds[2],
            'takedown defense':stats[5].strip(),
            'subs per 15min': stats[3].strip()
        }
    }
    return fighter

def search(query):
    url = 'https://www.google.com/search?q=' + query
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"}
    htm = req.get(url, headers = headers)
    xml = html.document_fromstring(htm.content)
    return xml.xpath("//h3/parent::a/@href")

def get_sherdog_link(query):
    possible_urls = search(query+" Sherdog")
    for url in possible_urls:
        if ("sherdog.com/fighter/" in url) and (not "/news/" in url):
            return url
    raise BaseException("Sherdog link not found !")
    
def get_ufc_link(query):
    possible_urls = search(query+" UFC.com")
    for url in possible_urls:
        if ("ufc.com/athlete/" in url):
            return url
    raise BaseException("UFC link not found !")
    
def get_fighter(query):
    sherdog_link = get_sherdog_link(query)
    ufc_link = get_ufc_link(query)
    
    fighter = parse_sherdog_fighter(sherdog_link)
    fighter.update(get_ufc_stats(ufc_link))
    return fighter


def get_upcoming_event_links():
    url = 'https://www.ufc.com/events'
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"}
    htm = req.get(url, headers = headers)
    xml = html.document_fromstring(htm.content)
    return ["https://www.ufc.com/"+x for x in xml.xpath("//details[@id='events-list-upcoming']/div/div/div/div/div/section/ul/li/article/div[1]/div/a/@href")]

def get_ufc_link_event(query):
    possible_urls = search(query+" UFC")
    for url in possible_urls:
        if ("ufc.com/event/" in url):
            return url
    raise BaseException("UFC link not found !")
    
def get_ranking(fight, corner):
    if corner == 'red':
        path = "div/div/div/div[2]/div[2]/div[2]/div[1]/span/text()"
    else:
        path = "div/div/div/div[2]/div[2]/div[2]/div[2]/span/text()"
        
    try:
        return fight.xpath(path)[0][1:]
    except IndexError:
        return "Unranked"
    
def get_name(fight, corner):
    if corner == 'red':
        path = "div/div/div/div[2]/div[2]/div[5]/div[1]/a/span/text()"
    else:
        path = "div/div/div/div[2]/div[2]/div[5]/div[3]/a/span/text()"
        
    name = " ".join(fight.xpath(path))
    
    if name == '':
        path = path.replace("/span", "")
        name = " ".join(fight.xpath(path)).strip()
    
    return name

def parse_event(url, past=True):
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"}
    htm = req.get(url, headers = headers)
    xml = html.document_fromstring(htm.content)
    fights_html = xml.xpath("//div[@class='fight-card']/div/div/section/ul/li")
    
    prefix = xml.xpath("//div[@class='c-hero__header']/div[1]/div/h1/text()")[0].strip()
    names = xml.xpath("//div[@class='c-hero__header']/div[2]/span/span/text()")

    name = f"{prefix}: {names[0].strip()} vs. {names[-1].strip()}"

    date = dt.datetime.fromtimestamp(int(xml.xpath("//div[@class='c-hero__bottom-text']/div[1]/@data-timestamp")[0]))
    date = date.strftime("%Y-%m-%d")
    location = xml.xpath("//div[@class='c-hero__bottom-text']/div[2]/div/text()")[0].split(",")

    event = {
        'name': name,
        'date': date,
        'location': location[1].strip(),
        'venue': location[0].strip(),
        'fights': []
    }
    for fight in fights_html:
        this_fight = {
                'weightclass': fight.xpath("div/div/div/div[2]/div[2]/div[1]/div[2]/text()")[0][:-5],
                'red corner': {
                    'name': get_name(fight, 'red'),
                    'ranking': get_ranking(fight, 'red'),
                    'odds': fight.xpath("div/div/div/div[4]/div[2]/span[1]/span/text()")[0],
                    'link': fight.xpath("div/div/div/div[2]/div[2]/div[5]/div[1]/a/@href")[0]
                },
                'blue corner': {
                    'name': get_name(fight, 'blue'),
                    'ranking': get_ranking(fight, 'blue'),
                    'odds': fight.xpath("div/div/div/div[4]/div[2]/span[3]/span/text()")[0],
                    'link': fight.xpath("div/div/div/div[2]/div[2]/div[5]/div[3]/a/@href")[0]            
                }
            }
        if past:
            result = fight.xpath("div/div/div/div[2]//div[@class='c-listing-fight__outcome-wrapper']/div/text()")
            method = fight.xpath("div//div[@class='c-listing-fight__result-text method']/text()")
            
            finished_round = fight.xpath("div//div[@class='c-listing-fight__result-text round']/text()")
            finished_time = fight.xpath("div//div[@class='c-listing-fight__result-text time']/text()")
            
            this_fight['round'] = finished_round[0]
            this_fight['time'] = finished_time[0]
            this_fight['method'] = method[0]
            this_fight['red corner']['result'] = result[0].strip()
            this_fight['blue corner']['result'] = result[1].strip()
        event['fights'].append(this_fight)
    return event

def get_upcoming_events():
    links = get_upcoming_event_links()
    
    results = {}
    
    for url in links:
        event = parse_event(url, False)
        results[event['name']] = event
    return results

def get_event(query):
    link = get_ufc_link_event(query)
    return parse_event(link)