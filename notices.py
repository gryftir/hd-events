from google.appengine.api import mail
from google.appengine.ext import deferred
import random
import os
import unicodedata
import re

FROM_ADDRESS = 'Dojo Events <robot@hackerdojo.com>'
NEW_EVENT_ADDRESS = 'events@hackerdojo.com'
STAFF_ADDRESS = 'staff@hackerdojo.com'

def slugify(str):
    str = unicodedata.normalize('NFKD', str.lower()).encode('ascii','ignore')
    return re.sub(r'\W+','-',str)

if os.environ['SERVER_SOFTWARE'].startswith('Dev'):
    MAIL_OVERRIDE = "nowhere@nowhere.com"
else:
    MAIL_OVERRIDE = False

def bug_owner_pending(e):
  body = """
Event: %s
Owner: %s
Date: %s
URL: http://%s/event/%s-%s
""" % (
    e.name,
    str(e.member),
    e.start_time.strftime('%A, %B %d'),
    os.environ.get('HTTP_HOST'),
    e.key().id(),
    slugify(e.name),)

  if not e.is_approved():
    body += """
Alert! The events team has not approved your event yet.
Please e-mail them at events@hackerdojo.com to see whats up.
"""

  body += """

Cheers,
Hacker Dojo Events Team
events@hackerdojo.com
"""

  deferred.defer(mail.send_mail, sender=FROM_ADDRESS, to=possibly_OVERRIDE_to_address(e.member.email()),
   subject="[Pending Event] Your event is still pending: " + e.name,
   body=body, _queue="emailthrottle")

def schedule_reminder_email(e):
  body = """

*REMINDER*

Event: %s
Owner: %s
Date: %s
URL: http://%s/event/%s-%s
""" % (
    e.name,
    str(e.owner()),
    e.start_time.strftime('%A, %B %d'),
    os.environ.get('HTTP_HOST'),
    e.key().id(),
    slugify(e.name),)
  body += """

Hello!  Friendly reminder that your event is scheduled to happen at Hacker Dojo.

 * The person named above must be physically present for the duration of the event
 * If the event has been cancelled, resecheduled or moved, you must login and cancel the event on our system

Cheers,
Hacker Dojo Events Team
events@hackerdojo.com

"""

  deferred.defer(mail.send_mail, sender=FROM_ADDRESS, to=possibly_OVERRIDE_to_address(e.member.email()),
   subject="[Event Reminder] " + e.name,
   body=body, _queue="emailthrottle")

def notify_owner_confirmation(event):
    deferred.defer(mail.send_mail ,sender=FROM_ADDRESS, to=possibly_OVERRIDE_to_address(event.member.email()),
        subject="[New Event] Submitted but **not yet approved**",
        body="""This is a confirmation that your event:

%s
on %s

has been submitted to be approved. You will be notified as soon as it's
approved and on the calendar. Here is a link to the event page:

http://events.hackerdojo.com/event/%s-%s

Again, your event is NOT YET APPROVED and not on the calendar.

Cheers,
Hacker Dojo Events Team
events@hackerdojo.com

""" % (
    event.name,
    event.start_time.strftime('%A, %B %d'),
    event.key().id(),
    slugify(event.name),))

def notify_event_change(event,old_event=None):
    if (old_event):
      subject = "[Event Modified]"
    else:
      subject = "[New Event]"
    mail_body = event.get_email_text(old_event)
    subject  += ' %s on %s' % (event.name, event.human_time())
    deferred.defer(mail.send_mail, sender=FROM_ADDRESS, to=possibly_OVERRIDE_to_address(NEW_EVENT_ADDRESS),
        subject=subject, body= mail_body)


def notify_owner_approved(event):
    deferred.defer(mail.send_mail,sender=FROM_ADDRESS, to=possibly_OVERRIDE_to_address(event.member.email()),
        subject="[Event Approved] %s" % event.name,
        body="""Your event is approved and on the calendar!

Friendly Reminder: You must be present at the event and make sure Dojo policies are followed.

Note: If you cancel or reschedule the event, please log in to our system and cancel the event!

http://events.hackerdojo.com/event/%s-%s

Cheers,
Hacker Dojo Events Team
events@hackerdojo.com

""" % (event.key().id(), slugify(event.name)))

def notify_owner_rsvp(event,user):
    deferred.defer(mail.send_mail,sender=FROM_ADDRESS, to=possibly_OVERRIDE_to_address(event.member.email()),
        subject="[Event RSVP] %s" % event.name,
        body="""Good news!  %s <%s> has RSVPd to your event.

Friendly Reminder: As per policy, all members are welcome to sit in on any event at Hacker Dojo.

As a courtesy, the Event RSVP system was built such that event hosts won't be surprised by the number of members attending their event.  Members can RSVP up to 48 hours before the event, after that the RSVP list is locked.

http://events.hackerdojo.com/event/%s-%s

Cheers,
Hacker Dojo Events Team
events@hackerdojo.com

""" % (user.nickname(),user.email(),event.key().id(), slugify(event.name)))

def notify_deletion(event,user):

    deferred.defer(mail.send_mail,sender=FROM_ADDRESS, to=possibly_OVERRIDE_to_address(event.member.email()),
        subject="[Event Deleted] %s" % event.name,
        body="""This event has been deleted.

http://events.hackerdojo.com/event/%s-%s

Cheers,
Hacker Dojo Events Team
events@hackerdojo.com

""" % (event.key().id(), slugify(event.name)))

def possibly_OVERRIDE_to_address(default):
    if MAIL_OVERRIDE:
        return MAIL_OVERRIDE
    else:
        return default

def notify_owner_expiring(event):
    pass

def notify_owner_expired(event):
    pass

def notify_hvac_change(iat,mode):
  body = """

The inside air temperature was %d.  HVAC is now set to %s.

""" % (iat,mode)

  deferred.defer(mail.send_mail, sender=FROM_ADDRESS, to=possibly_OVERRIDE_to_address("hvac-operations@hackerdojo.com"),
   subject="[HVAC auto-pilot] " + mode,
   body=body, _queue="emailthrottle")
