"""
Ask Alexa to get your Current Glucose Reading
"""

from __future__ import print_function
import urllib2, urllib
import json

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Dexcom Glucose Skill. " \
                    "Please tell me you want me to read your glucose number by saying, " \
                    "tell me my glucose or my glucose."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "I did not understand. Please tell me you want me to read your glucose number by saying, " \
                    "tell me my glucose or my glucose."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Have a nice day! "
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def get_my_glucose_in_session(intent, session):
    card_title = intent['name']
    should_end_session = True
    method = "POST"
    handler = urllib2.HTTPHandler()
    opener = urllib2.build_opener(handler)
    sessionIdUrl = 'https://share1.dexcom.com/ShareWebServices/Services/General/LoginPublisherAccountByName'
    glucoseUrl = 'https://share1.dexcom.com/ShareWebServices/Services/Publisher/ReadPublisherLatestGlucoseValues?sessionID='
    glucoseGetParams = '&minutes=1440&maxCount=1'
    payload ={"password": "YOUR_PASSWORD", "applicationId" : "d89443d2-327c-4a6f-89e5-496bbb0317db", "accountName": "YOUR_ACCOUNT_NAME"}
    seshRequest = urllib2.Request(sessionIdUrl, json.dumps(payload))
    
    seshRequest.add_header("Content-Type",'application/json')
    seshRequest.add_header("User-Agent",'Dexcom Share/3.0.2.11 CFNetwork/672.0.2 Darwin/14.0.0')
    seshRequest.add_header("Accept",'application/json')
    seshRequest.get_method = lambda: method
    #Get your session ID
    try:
        connection = opener.open(seshRequest)
    except urllib2.HTTPError,e:
        connection = e
    if connection.code == 200:
        sessionID = connection.read()
        #Strip Qoutes
        sessionID = sessionID[1:-1]
    else:
        print(connection.code)
        
    #Get your glucose reading
    getGlucoseUrl = glucoseUrl + sessionID + glucoseGetParams
    
    glucoseRequest = urllib2.Request(getGlucoseUrl)
    glucoseRequest.get_method = lambda: method
    glucoseRequest.add_header("Accept",'application/json')
    glucoseRequest.add_header("Content-Length",'0')
    emptyLoad ={"":""}
    try:
        #POST to Service with an empty payload or else you'll get a 405
        connection2 = opener.open(glucoseRequest, json.dumps(emptyLoad)) 
    except urllib2.HTTPError,e:
        connection2 = e
    if connection.code == 200:
        glucoseReading = connection2.read()
        glucoseReading = json.loads(glucoseReading)
        glucose = glucoseReading[0]["Value"]
        trend = glucoseReading[0]["Trend"]
        
    else:
        print(connection2.code)
    
    if trend == 1:
        trendtext = "rising quickly"
    if trend == 2:
        trendtext = "rising"
    if trend == 3: 
        trendtext = "rising slightly"
    if trend == 4:
        trendtext = "steady"
    if trend == 5:
        trendtext = "falling slightly"
    if trend == 6:
        trendtext = "falling"
    if trend == 7:
        trendtext = "falling quickly"
    if trend == 8:
        trendtext = "unable to determine a trend"
    if trend == 9:
        trendtext = "trend unavailable"
        
    speech_output = "Your glucose is " + str(glucose) + "and " + str(trendtext)
   
    return build_response({},build_speechlet_response(
        card_title, speech_output, should_end_session))
# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "GetGlucoseNow":
        return get_my_glucose_in_session(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" 
    + event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

