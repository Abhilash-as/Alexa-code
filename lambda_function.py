
from __future__ import print_function
import random
import boto3
from boto3.dynamodb.conditions import Attr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def build_speechlet_response(title, output, reprompt_text, should_end_session):
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
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
   
    speech_output = "Welcome to the New Shopping Experience,What Would You Like to Shop."
  
   
    reprompt_text = "I didn't get that. Welcome to the New Shopping Experience,What Would You Like to Shop."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_session_end_request():
    session_attributes = {}
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Alexa Shopping " \
                    "Have a nice day! "
  
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def get_item_details(choice):
    dynamodb = boto3.resource('dynamodb')
    table=dynamodb.Table('shopp')
    response=table.scan(
        FilterExpression=Attr('items').eq(choice)
    )
    count = response['Items']
    a=[]
    for x in count:
        for y in x:
            if(y=='shop_name'):
                a.append(x[y])
    names = a[0] + " And " + a[1] 
    return names
  
def select_item_intent(intent, session):
    
    card_title = intent['name']
    reprompt_text = None
    choice = intent['slots']['choices']['value']
    speech_output = choice + "is available at " +  get_item_details(choice) + "\n\n\n Choose a shop" 
    session_attributes = {"choice1":choice , "shop_choices1":0}
    should_end_session=False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        

def shop_select_intent(intent, session):
    session_attributes = session["attributes"]
    choice2 = session_attributes["choice1"]
    card_title = intent['name']
    reprompt_text = None
    shop_choices = intent['slots']['shop_choice']['value']
    messages = "New order for " + choice2 + " at " + shop_choices
 
    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    EMAIL="yourmail@gmail.com"
    PASSWORD="password"
    server.login(EMAIL,PASSWORD)
    message=MIMEText(messages)
    message["From"]=EMAIL
    message["To"]=EMAIL
    message["Subject"]="New Order"
    
    server.sendmail(EMAIL,EMAIL,message.as_string()) 
    
    speech_output = "Order placed"
    session_attributes["shop_choices1"] = shop_choices
    should_end_session=False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        

def on_session_started(session_started_request, session):
    """ Called when the session starts """
   
    
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
   

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    
    return get_welcome_response()

def on_intent(intent_request, session):
    

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    
   
    if intent_name == "select_item":
        return select_item_intent(intent, session)
    elif intent_name == "shop_select":
        return shop_select_intent(intent,session)
    elif intent_name == "AMAZON.CancelIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    


# --------------- Main handler ------------------

def lambda_handler(event, context):
    
    print("event.session.application.applicationId=" +
        event['session']['application']['applicationId'])
    
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

