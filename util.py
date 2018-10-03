import requests
from bs4 import BeautifulSoup
from lxml import etree
from os.path import join
from pandas import read_html


cap_friendly_base_url = 'http://capfriendly.com/player/'

all_categories = {'position': '/html/body/div[7]/div/div/div[1]/h6[2]/text()',
                  'birthday':'/html/body/div[7]/div/div/div[3]/div[1]/text()',
                  'birthplace':'/html/body/div[7]/div/div/div[3]/div[2]/text()',
                  'height':'/html/body/div[7]/div/div/div[3]/div[3]/text()',
                  'weight':'/html/body/div[7]/div/div/div[3]/div[4]/text()',
                  'age':'/html/body/div[7]/div/div/div[4]/div[2]/text()',
                  'draft_year':'//*[@id="pld_c3"]/div[1]/text()',
                  'draft_team': '//*[@id="pld_c3"]/div[4]/text()',
                  'draft_overall':'//*[@id="pld_c3"]/div[2]/text()'}

contract_cateogries = ['CLAUSE', 'CAP HIT', 'AAV', 'P. BONUSES', 'S. BONUSES', 'BASE SALARY', 'TOTAL SALARY']

skater_categories = ['Team', 'G', 'A', 'TP', 'GP', 'PIM']

goalie_categories = ['Team', 'GP','GAA', 'SVS%']

pnf_string = 'Player not found'

practice_strings = ['Where does Erik Karlsson play?',
                    'Where did John Tavares play in 2013?',
                    'What was Drew Doughty\'s cap hit in 14?',
                    'How many goals did Joe Pavelski score in 2016?',
                    'Where was Connor McDavid born?',
                    'How tall is Ryan Getzlaf?',
                    'What team drafted Roberto Luongo?',
                    'What position does Marc-Eduard Vlasic play?',
                    'What about Connor McDavid?',
                    'Jesus Christ']


html_parser = etree.HTMLParser()

question_words = ['what', 'how', 'where', 'who', 'does',  'can', 'whose', 'which',
                  'whom', 'when']


def parse_user_input(user_input=''):
    understanding = {}
    uil = user_input.lower()
    if 'fight on' in uil:
        understanding = {'easter_egg':'sc'}
        return understanding

    if 'jesus christ' in uil:
        understanding = {'easter_egg':'jb'}
        return understanding

    if 'hi ' in uil or 'hello ' in uil:
        understanding['greeting'] = True
        return understanding

    tokens = user_input.strip('?').split()
    understanding['player_name'] = []
    understanding['season'] = []
    for token in tokens:
        if token[0].isupper() and token.lower() not in question_words:
            if token[-2:] == "\'s":
                understanding['player_name'].append(token[:-2])
            else:
                understanding['player_name'].append(token)
        if token.isdigit():
            understanding['season'].append(token)

    understanding['player_name'] = ' '.join(understanding['player_name'])
    
    understanding['categories'] = []
    if 'born' in uil: #really unique query
        if 'where' in uil:
            understanding['categories'].append('birthplace')
        if 'when' in uil:
            understanding['categories'].append('birthday')
    
    elif 'drafted' in uil: # draft specific query
        if 'who' in uil or 'team' in uil:
            understanding['categories'].append('draft_team')

        if 'when' in uil or 'year' in uil:
            understanding['categories'].append('draft_year')

        if 'where' in uil or 'position' in uil or 'overall' in uil:
            understanding['categories'].append('draft_overall')

        if len(understanding['categories']) == 0:
            understanding['categories'] += ['draft_team', 'draft_year', 'draft_overall']


    elif 'team' in uil or ('where' in uil and 'play' in uil):
        understanding['categories'].append('Team')

    elif 'position' in uil:
        understanding['categories'].append('position')

    if 'old' in uil or 'age' in 'uil':
        understanding['categories'].append('age')

    if 'tall' in uil or 'height' in 'uil':
        understanding['categories'].append('height')

    if 'weigh' in uil:
        understanding['categories'].append('weight')

    if 'gaa' in uil or 'goals against' in uil:
        understanding['categories'].append('GAA')
    elif 'goals' in uil:
        understanding['categories'].append('G')

    if 'save' in uil or '%' in uil:
        understanding['categories'].append('SVS%')

    if 'assists' in uil or 'apples' in uil:
        understanding['categories'].append('A')

    if 'penalities' in uil or 'pim' in uil:
        understanding['categories'].append('PIM')

    if 'games played' in uil or 'gp' in uil:
        understanding['categories'].append('GP')

    if 'points' in uil in uil:
        understanding['categories'].append('TP')

    for c in contract_cateogries:
        if c.lower() in uil:
            understanding['categories'].append(c)

    if 'performance bonus' in uil:
        understanding['categories'].append('P. BONUSES')

    if 'signing bonus' in uil:
        understanding['categories'].append('S. BONUSES')

    if 'playoff' in uil:
        understanding['playoff']  = True

    return understanding


def get_stats(player_name, categories, season, playoff=False):
    # print(playoff)
    name_to_url = '-'.join(player_name.lower().split())
    get_url = join(cap_friendly_base_url, name_to_url)
    capfriendly_request = requests.get(get_url)

    output = {'request_status':(capfriendly_request.status_code == 200),
              'player_found':False}

    if capfriendly_request.status_code == 200: #Successfully exectued GET
        html_doc = etree.fromstring(capfriendly_request.text, html_parser)
        html_soup = BeautifulSoup(capfriendly_request.text, 'lxml')
        if html_soup.body.h1.text != pnf_string:
            output['player_found'] = True
            output['position'] = html_doc.xpath(all_categories['position'])[0]
            tables = html_soup.body.findChildren('table')
            last_table_idx = len(tables) - 1
            current_contract_table = read_html(str(tables[0]), header=0, index_col=0)[0]
            career_stats_table = read_html(str(tables[last_table_idx]), header=0, index_col=0)[0]

            for c in categories:
                if c in all_categories:
                    output[c] = html_doc.xpath(all_categories[c])
                    if output[c] is not None and len(output[c]) > 0:
                        output[c] = output[c][0]
                elif c in contract_cateogries:
                    # print('accessing contract categories')
                    output[c] = current_contract_table.get(c)
                    # print('output', output[c])
                    if output[c] is not None:
                        # print('made it here')
                        output[c] = output[c].get(season[0])
                elif c in skater_categories or c in goalie_categories:
                    c_name = c if not playoff else (c + '.1')
                    output[c] = career_stats_table.get(c_name)

                    # print('accessing states categories')
                    # print('output', output[c])

                    if output[c] is not None:
                        output[c] = output[c].get(season[1])

                else:
                    output[c] = 'invalid'

    return output


if __name__ == '__main__':
    # Test script
    print('Beginning util test')
    print("importing 'random'")
    from numpy.random import choice, randint
    print('constructing player - stat splits')
    player_names = ['Erik Karlsson', 'Gritty', 'Craig Anderson',
                    'John Tavares', 'Brock Boeser', 'Evgeni Nabokov']

    print('generating requests')
    categories_per_player = [randint(1, 5) for name in player_names]

    for i in range(len(player_names)):
        choices = choice(list(all_categories.keys()) +\
                         contract_cateogries +\
                         skater_categories + \
                         goalie_categories, categories_per_player[i], replace=False)
        print(player_names[i])
        print('\t', choices)
        out = get_stats(player_names[i], choices, ['2017-18', '2017-2018'], playoff=bool(randint(0, 2)))
        print('\t', out)

    print('data access tests completed')
    print('\n\n')
    print('starting nlp tests')

    for s in practice_strings:
        print(s)
        print('\t', parse_user_input(s))