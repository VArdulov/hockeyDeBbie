from util import get_stats, parse_user_input

opening_message = "Hi there!\n"+\
                  "My name is DeBbie, I'm a conversational agent that answers some hockey player trivia\n"+\
                  "I'm still kind of new to all of this so go a little easy on me :)\n\n"+\
                  "I can answer some information about players\n" +\
                  "\tlike GP or total points from the season or play-off run\n"+\
                  "\tor the AAV or total salary for current contracts players hold\n"+\
                  "\tor maybe their birthday or draft year\n\n"+\
                  "Just make sure to spell properly, I'm only a week old\n"+\
                  "so I'm still getting the hang of this whole __natural_language__ thing!"

draft_answer_base = '%s was drafted'
draft_answer_append = {'draft_year': 'in %s', 'draft_overall':'%s overall', 'draft_team':'by %s'}

born_answer_base = '%s was born'
born_answer_append = {'birthplace': 'in %s', 'birthday': 'on %s'}


stat_answer_base = 'In %s, %s'
templates = {'GP': 'played in %s games',
              'Team': 'played for %s',
              'G': 'scored %s goals',
              'A': 'assisted on %s goals',
              'TP': 'scored %s total points',
              'GAA': 'gave up %s goals on average',
              'SVS%': 'had a save-percentage of %s',
              'CAP HIT': 'had a cap hit of %s',
              'AAV': 'had an AAV of %s',
              'CLAUSE':'had a %s contract clause',
              'P. BONUSES':'had a performance bonus of %s',
              'S. BONUSES':'had a signing bonus of %s',
              'BASE SALARY':'had a base salary of %s',
              'TOTAL SALARY': 'made a total salary of %s'}

ask_for_clarification = "I'm sorry, I didn't quite understand what you were asking, can you try rephrasing the question?"

clarify_year = 'What season are you asking about?'
clarify_player = 'What player are you asking about?'
clarify_category = 'What categories are you asking about?'

connection_problem = "I'm sorry I can't connect to my database right now :( Mayeb try again later or check you connection"

good_bye = 'Thanks for chatting! Long live the robots!'

easter_eggs = {'sc':"Fight On for Ol' SC!",
               'jb': "IT'S JASON BOURNE!"}

default_year = ['2018-19', '2018-2019']

def construct_response_update_state(user_input, current_state):
    new_state = {}
    response = ''
    if 'easter_egg' in user_input:
        return (current_state, easter_eggs[user_input['easter_egg']])

    if 'categories' in user_input and len(user_input['categories']) > 0:
        new_state['categories'] = user_input['categories']
    elif 'categories' in current_state and len(current_state['categories']) > 0:
        new_state['categories'] = current_state['categories']
    else:
        response = clarify_category
        
    if 'player_name' in user_input and len(user_input['player_name']) > 0:
        new_state['player_name'] = user_input['player_name']
    elif 'player_name' in current_state and len(current_state['player_name']) > 0:
        new_state['player_name'] = current_state['player_name']
    else:
        response = clarify_player

    if 'season' in user_input and len(user_input['season']) > 0:
        season = user_input['season'][0]
        # print('season' season)
        if len(season) < 4:
            if int(season) < 25:
                season = '20' + season
            else:
                season = '19' + season

        season = int(season)
        if season > 2000:
            season = ['%d-%d'%(season, (season+1)-2000),
                      '%d-%d'%(season, (season+1))]
        else:
            season = ['%d-%d' % (season, (season + 1) - 1900),
                      '%d-%d' % (season, (season + 1))]

        new_state['season'] = season
    elif 'season' in current_state and len(current_state['season']) > 0:
        new_state['season'] = current_state['season']
    else:
        new_state['season'] = default_year

    if new_state == current_state:
        print('here')
        response = ask_for_clarification

    if response == '':
        stats = get_stats(new_state['player_name'],
                          new_state['categories'],
                          new_state['season'],
                          user_input.get('playoff', False))
        if stats['request_status']:
            if stats['player_found']:
                # print(stats)
                for c in new_state['categories']:
                    if c in born_answer_append:
                        if len(response) == 0:
                            response = born_answer_base%(new_state['player_name'])
                        response += ' ' + (born_answer_append[c]%(stats[c]))
                    elif c in draft_answer_append:
                        if len(response) == 0:
                            response = draft_answer_base % (new_state['player_name'])
                        response += ' ' + (draft_answer_append[c] % (stats[c] if stats[c] is not None else 'no'))
                    elif c in templates:
                        if len(response) == 0:
                            response = stat_answer_base%(new_state['season'][0], new_state['player_name'])
                            response += ' ' + (templates[c]%(stats[c] if stats[c] is not None else 'no'))
                        else:
                            response += ', and ' + (templates[c] % (stats[c] if stats[c] is not None else 'no'))
                        if user_input.get('playoff', False): response += ' during the playoffs'
                    elif c == 'weight':
                        if len(response) == 0:
                            response = new_state['player_name']
                        response += ' weighs %s'%(stats[c])
                    elif c == 'height':
                        if len(response) == 0:
                            response = new_state['player_name']
                        response += ' is %s'%(stats[c])
                    elif c == 'age':
                        if len(response) == 0:
                            response = new_state['player_name']
                        response += ' is %s years old'%(stats[c])
                    elif c == 'position':
                        if len(response) == 0:
                            response = new_state['player_name']
                        response += ' plays %s'%(stats[c])


            else:
                response = clarify_player

        else:
            response = connection_problem

    return (new_state, response)

def chat(current_state):
    #wait for user input
    user_input = input('>')
    user_input = parse_user_input(user_input)
    return construct_response_update_state(user_input, current_state)

if __name__ == '__main__':
    good_bye_status = False
    print(opening_message)
    state = {}
    while not good_bye_status:
        state, response = chat(state)
        print(response)
        # print('\t debug', state)
