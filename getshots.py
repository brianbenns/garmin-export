import requests, json, math, sys
from geopy import distance

cookie = ""
authorization = ""

def meters_to_yards(m):
    return m*1.093
def calculate_distance(a, b):
  multiplier = 180.0/math.pow(2,31) 
  ad = (a[0]*multiplier, a[1]*multiplier) #This converts garmins location unit to typical GPS
  bd = (b[0]*multiplier, b[1]*multiplier)
  return int(distance.distance(ad, bd).feet/3)

def main():
    clubTypeMap= {
        1: "Driver",
        2: "3 Wood",
        3: "5 wood",
        6: "3 Hybrid",
        7: "4 Hybrid",
        13: "4 Iron",
        14: "5 Iron",
        15: "6 Iron",
        16: "7 Iron",
        17: "8 Iron",
        18: "9 Iron",
        19: "Pitching Wedge",
        20: "Gap Wedge",
        21: "Sand Wedge",
        22: "Lob Wedge",
    }
    clubIdMap = {}

    shotsUrl = 'https://connect.garmin.com/modern/proxy/gcs-golfcommunity/api/v2/shot/scorecard/{}/hole?hole-numbers=1-2-3-4-5-6-7-8-9-10-11-12-13-14-15-16-17-18&image-size=IMG_730X730&_=1622302607109'
    cardsUrl = 'https://connect.garmin.com/modern/proxy/gcs-golfcommunity/api/v2/scorecard/summary?per-page=10000&user-locale=en&_=161588286562'
    cardUrl = 'https://connect.garmin.com/modern/proxy/gcs-golfcommunity/api/v2/scorecard/{}'
    clubsUrl = 'https://connect.garmin.com/gcs-golfcommunity/api/v2/club/player?per-page=1000&include-stats=false&maxClubTypeId=42'
    headers = {
        'nk': 'NT',
        'cookie': cookie
    }
    clubs_headers = {
        'nk': 'NT',
        'authorization': authorization,
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'di-backend': 'golf.garmin.com'
    }

    r = requests.get(headers=headers, url=cardsUrl)

    ids = []
    if r.status_code == 200:
        cardSummaries = json.loads(r.text)['scorecardSummaries']
        for card in cardSummaries:
            ids.append(card['id'])
    else:
        print("Could not get scorecard IDs, exiting.")
        sys.exit(1)

    r = requests.get(headers=clubs_headers, url=clubsUrl)
    if r.status_code == 200:
        clubs = json.loads(r.text)
        for club in clubs:
            if "name" in club:
                clubIdMap[club["id"]] = club["name"]
            elif club["clubTypeId"] in clubTypeMap:
                clubIdMap[club["id"]] = clubTypeMap[club["clubTypeId"]]
    else:
        print("Could not get club name information. Clubs will be labeled as 'unknown'")

    with open('shots.csv', 'w') as f:
        f.write("club,hole_num,shot_num,start_dis_to_pin,start_lie,end_dis_to_pin,end_lie,shot_dis,shot_type,end_x,end_y,score,scorecard_url")
        print("Downloading shot data, this could take a while...")
        i = 0
        for id in ids:
            url = shotsUrl.format(id)
            r = requests.get(headers=headers, url=url)
            if r.status_code == 200:
                shots = json.loads(r.text)
                shots = shots['holeShots']
                r = requests.get(headers=headers, url=cardUrl.format(id))
                scorecard = json.loads(r.text)
                for hole in shots:
                    pinPosLat = hole['pinPosition']['lat']
                    pinPosLon = hole['pinPosition']['lon']
                    if 'shots' in hole:
                        for shot in hole['shots']:
                            i+=1
                            if i % 250 == 0:
                                print("Downloaded {} shots so far.".format(i))
                            try:
                                if shot['clubId'] in clubIdMap:
                                    club = clubIdMap[shot['clubId']]
                                else:
                                    club = 'unknown'
                                pin_pos = (hole['pinPosition']['lat'], hole['pinPosition']['lon'])
                                start_pos = (shot['startLoc']['lat'], shot['startLoc']['lon']) 
                                end_pos = (shot['endLoc']['lat'], shot['endLoc']['lon'])
                                start_dist_to_pin = calculate_distance(start_pos, pin_pos)
                                end_dist_to_pin = calculate_distance(end_pos, pin_pos)
                                end_x = shot['endLoc']['x']
                                end_y = shot['endLoc']['y']
                                score = scorecard['holes'][hole['holeNumber']-1]['strokes']
                                row = '{},{},{},{},{},{},{},{},{},{},{},{},{}\n'.format(
                                    club, hole['holeNumber'], shot['shotOrder'], 
                                    start_dist_to_pin, shot['startLoc']['lie'], end_dist_to_pin, shot['endLoc']['lie'], meters_to_yards(shot['meters']),
                                    shot['shotType'], end_x, end_y, score, 'https://connect.garmin.com/modern/scorecard/{}'.format(id))
                                f.write(row)
                            except KeyError:
                                continue

                        
            else:
                continue
                
        else:
            print("Could not get scorecard id: {}".format(id))

if __name__ == "__main__":
    main()