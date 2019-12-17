from model import db, Event, Calendar, User, UserCal, CalEvent
from flask import jsonify


def seed_user(profile, user_id):

    first_name = profile['names'][0].get("givenName")
    last_name = profile['names'][0].get("familyName")

    user_exists = User.query.get(user_id)

    if user_exists is None:

        user = User(user_id=user_id,
                    first_name=first_name,
                    last_name=last_name)

        db.session.add(user)
        db.session.commit()

    return user_id


def seed_calendars(calendars, user_id):

    for calendar in calendars.values():

        calendar_id = calendar['id'].lower()
        timezone = calendar['timeZone']
        summary = calendar['summary']
        etag = calendar['etag']

        if 'primary' in calendar:
            primary = calendar['primary']

        else:
            primary = False

        if 'selected' in calendar:
            selected = calendar['selected']

        else:
            selected = False

        cal_exists = Calendar.query.get(calendar_id)
        usercal_exists = UserCal.query.filter_by(user_id=user_id,
                                                 calendar_id=calendar_id).first()

        if cal_exists and usercal_exists is None:

            usercal = UserCal(user_id=user_id,
                              calendar_id=calendar_id,
                              primary=primary,
                              selected=selected)

            db.session.add(usercal)
            db.session.commit()

        elif cal_exists is None:

            calendar_obj = Calendar(calendar_id=calendar_id,
                                    etag=etag,
                                    summary=summary,
                                    timezone=timezone)

            db.session.add(calendar_obj)
            db.session.commit()

            usercal = UserCal(user_id=user_id,
                              calendar_id=calendar_id,
                              primary=primary,
                              selected=selected)

            db.session.add(usercal)
            db.session.commit()

    return calendar_id



def seed_events(events, colors, calendar_colors):

    event_colors = {k: v['background'] for k, v in colors['event'].items()}

    '''Event labels'''
    college_administration = [event_colors["9"], "College Administration"]      #Blueberry
    development = [event_colors["7"], "Development"]                            #Peacock
    major_projects = [event_colors["6"], "Major Projects (DEI/Hub/Digital Studies/Quantitative Social Sciences/Associate Professor Rank Committee)"]                      #Tangerine
    outreach = [calendar_colors['dean'], "Outreach"]                            #Dean calendar color for default-colored events
    outside_umich_professional = [event_colors["2"], "Outside U-M Professional Activities"] #Sage
    personal_time = [event_colors["3"], "Personal Time"]                        #Grape
    university_administration = [event_colors["10"], "University Administration"] #Basil

    unlabeled = [event_colors["1"], "Lavender (unlabeled)"]                                  #Lavender
    unlabeled2 = [event_colors["4"], "Flamingo (unlabeled)"]                                #Flamingo
    unlabeled3 = [event_colors["5"], "Banana (unlabeled)"]                                  #Banana
    unlabeled4 = [event_colors["8"], "Graphite (unlabeled)"]                                #Graphite
    unlabeled5 = [event_colors["11"], "Tomato (unlabeled)"]                                 #Tomato
    #unlabeled6 = [calendar_colors['primary'], "Primary calendar color"]        #Primary calendar color for default-colored events

    def get_label(color):
        return {
            college_administration[0]: college_administration[1],
            development[0]: development[1],
            major_projects[0]: major_projects[1],
            outreach[0]: outreach[1],
            outside_umich_professional[0]: outside_umich_professional[1],
            personal_time[0]: personal_time[1],
            university_administration[0]: university_administration[1],

            unlabeled[0]: unlabeled[1],
            unlabeled2[0]: unlabeled2[1],
            unlabeled3[0]: unlabeled3[1],
            unlabeled4[0]: unlabeled4[1],
            unlabeled5[0]: unlabeled5[1],
            #unlabeled6[0]: unlabeled6[1]
        }.get(color, 0)

    for key, value in events.items():

        items = value.get('items', [])
        for event in items:

            etag = event['etag']
            event_id = event['id']
            creator = event['creator'].get('email', []).lower()
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = "None"
            color = event.setdefault('colorId', 0)
            if color in event_colors:
                color = event_colors[color]
                label = get_label(color)
            else:
                color = calendar_colors['dean']         #Default calendar color
                label = get_label(color)

            event_exists = Event.query.get(event_id)
            calevents_exists = CalEvent.query.filter_by(calendar_id=key,
                                                        event_id=event_id).first()

            if event_exists and calevents_exists is None:

                calevent = CalEvent(calendar_id=key,
                                    event_id=event_id)

                db.session.add(calevent)
                db.session.commit()

            elif event_exists is None:

                event_obj = Event(event_id=event_id,
                                  etag=etag,
                                  creator=creator,
                                  start=start,
                                  end=end,
                                  summary=summary,
                                  color=color,
                                  label=label)

                db.session.add(event_obj)
                db.session.commit()

                calevent = CalEvent(calendar_id=key,
                                    event_id=event_id)

                db.session.add(calevent)
                db.session.commit()
