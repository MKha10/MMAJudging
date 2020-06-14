import requests
from bs4 import BeautifulSoup
import numpy as np

url = 'http://mmadecisions.com/decision/10877/Jon-Jones-vs-Dominick-Reyes'
r = requests.get(url)
soup = BeautifulSoup(r.content, 'html.parser')


# finding the fight name/result
def fight_result_finder(s):
    metadata = {}
    f1_name = s.find_all("td",
                         {'class': 'decision-top'})[0].find('a').text.strip().replace('\xa0', ' ')
    f2_name = s.find_all("td",
                         {'class': 'decision-bottom'})[1].find('a').text.strip().replace('\xa0', ' ')
    fight_decision = soup.find_all("td",
                                   {'class': 'decision-middle'})[0].text.strip()
    metadata.update(
        {'result': f1_name + ' ' + fight_decision + ' ' + f2_name,
         'first_fighter': f1_name,
         'second_fighter': f2_name})
    return metadata


result_data = fight_result_finder(soup)
fighter1 = result_data.get('first_fighter')
fighter2 = result_data.get('second_fighter')
fighter1_first_name = fighter1.split()[0]
fighter1_last_name = fighter1[len(fighter1_first_name):]
fighter2_first_name = fighter2.split()[0]
fighter2_last_name = fighter2[len(fighter2_first_name):]
result = result_data.get('result')


# finding location, event, and date of the fight
def fight_metadata(s):
    metadata = {}
    evt = s.find_all('td',
                     {'class': 'decision-top2'})[0].find('b').find('a').text
    loc = s.find_all('td', {'class': 'decision-top2'})[0].contents[5].strip()
    dt = s.find_all('td', {'class': 'decision-top2'})[0].contents[3].strip()
    metadata.update({'event': evt, 'location': loc, 'date': dt})
    return metadata


event_metadata = fight_metadata(soup)
event_name = event_metadata.get('event')
event_location = event_metadata.get('location')
event_date = event_metadata.get('date')

# gives data for judging for the first and second fighter
judges_data = soup.find_all("td", {'class': 'judge'})
scores_data = soup.find_all('td', {'class': 'bottom-cell'})


def f1_judging_data(judges, scores):
    metadata = {}
    metadata.update({judges[0].text.strip().replace('\xa0', ' '): int(scores[0].text),
                     judges[1].text.strip().replace('\xa0', ' '): int(scores[2].text),
                     judges[2].text.strip().replace('\xa0', ' '): int(scores[4].text)})
    return metadata


def f2_judging_data(judges, scores):
    metadata = {}
    metadata.update({judges[0].text.strip().replace('\xa0', ' '): int(scores[1].text),
                     judges[1].text.strip().replace('\xa0', ' '): int(scores[3].text),
                     judges[2].text.strip().replace('\xa0', ' '): int(scores[5].text)})
    return metadata


f1_judge_scores = f1_judging_data(judges_data, scores_data)
f2_judge_scores = f2_judging_data(judges_data, scores_data)

# gives data on media judging for the first and second fighter
media_tbl_data = soup.find(text="MEDIA SCORES").find_parent('table')


def f1_media(media_tbl):
    metadata = []
    for rw in media_tbl.find_all('tr')[1:]:
        cells = rw.find_all('td')
        try:
            metadata.append(int(cells[1].text.strip()[0:2]))
        except IndexError:
            continue
    return np.array(metadata)


def f2_media(media_tbl):
    metadata = []
    for rw in media_tbl.find_all('tr')[1:]:
        cells = rw.find_all('td')
        try:
            metadata.append(int(cells[1].text.strip()[3:]))
        except IndexError:
            continue
    return np.array(metadata)


f1_media_scores = f1_media(media_tbl_data)
f2_media_scores = f2_media(media_tbl_data)
number_of_media = len(f1_media_scores)

# gives data on fan judging for the first and second fighter
fan_result_rows = soup.find(text='FAN SCORING').find_parent('table').find_all('tr')[1].find_all('tr')


def fan_proportions(rows):
    fighter1_fans = {}
    fighter2_fans = {}
    for rw in rows:
        cells = rw.find_all('td')
        fight_decision = cells[0].get_text()
        if 'defeats' in fight_decision:
            proportion = float(cells[2].get_text()[:-1]) / 100

            winner = fight_decision.split(' defeats ')[0]
            winner_score = int(cells[1].get_text()[0:2])

            loser = fight_decision.split(' defeats ')[1]
            loser_score = int(cells[1].get_text()[5:7])

            if winner in fighter1_last_name:
                if winner_score in fighter1_fans:
                    fighter1_fans[winner_score] += proportion
                else:
                    fighter1_fans[winner_score] = proportion

                if loser_score in fighter2_fans:
                    fighter2_fans[loser_score] += proportion
                else:
                    fighter2_fans[loser_score] = proportion
            else:
                if winner_score in fighter2_fans:
                    fighter2_fans[winner_score] += proportion
                else:
                    fighter2_fans[winner_score] = proportion

                if loser_score in fighter1_fans:
                    fighter1_fans[loser_score] += proportion
                else:
                    fighter1_fans[loser_score] = proportion
        if 'draws with' in fight_decision:
            proportion = float(cells[2].get_text()[:-1]) / 100
            both_score = int(cells[1].get_text()[0:2])

            if both_score in fighter1_fans:
                fighter1_fans[both_score] += proportion
            else:
                fighter1_fans[both_score] = proportion

            if both_score in fighter2_fans:
                fighter2_fans[both_score] += proportion
            else:
                fighter2_fans[both_score] = proportion
    return fighter1_fans, fighter2_fans


def fans_raw(props):
    num_fans_original = int(soup.find('div', {'id': 'scorecards_submitted'}).find('b').get_text())
    f1_len = 0
    f2_len = 0
    for val in props[0].values():
        f1_len += int(round(val * num_fans_original))
    for val in props[1].values():
        f2_len += int(round(val * num_fans_original))
    f1_raw = np.zeros(f1_len)
    f2_raw = np.zeros(f2_len)
    curr1 = 0
    curr2 = 0
    for k in props[0].keys():
        number_of_scores = int(round(props[0].get(k) * num_fans_original))
        f1_raw[curr1:curr1 + number_of_scores] = k
        curr1 += number_of_scores
    for k in props[1].keys():
        number_of_scores = int(round(props[1].get(k) * num_fans_original))
        f2_raw[curr2:curr2 + number_of_scores] = k
        curr2 += number_of_scores
    return f1_raw, f2_raw, f1_len


fan_proportion_results = fan_proportions(fan_result_rows)
f1_fan_proportions = fan_proportion_results[0]
f2_fan_proportions = fan_proportion_results[1]
fan_raw_stats = fans_raw(fan_proportion_results)
f1_fans_raw_numbers = fan_raw_stats[0]
f2_fans_raw_numbers = fan_raw_stats[1]
num_fans = fan_raw_stats[2]

fight_summary = {'Fight Decision': result,
                 'Date': event_date,
                 'Location': event_location,
                 'Event': event_name,
                 'Fighter 1': fighter1,
                 'Fighter 2': fighter2,
                 'Raw Fan Scores for Fighter 1': f1_fans_raw_numbers,
                 'Raw Fan Scores for Fighter 2': f2_fans_raw_numbers,
                 'Proportional Fan Scores for Fighter 1': f1_fan_proportions,
                 'Proportional Fan Scores for Fighter 2': f2_fan_proportions,
                 'Number of Fans': num_fans,
                 'Fighter 1 Judge Scores': f1_judge_scores,
                 'Fighter 2 Judge Scores': f2_judge_scores,
                 'Fighter 1 Media Scores': f1_media_scores,
                 'Fighter 2 Media Scores': f2_media_scores,
                 'Number of Media Members': number_of_media}

