import json
import urllib2

def parse_text(text):#, sentences="MULTIPLE", ignoreSetneceLen=False ) :

    if text:
        if text != "":
            url = 'http://127.0.0.1:9000/?properties=%7B%22annotators%22:%20%22tokenize,ner%22,%20%22outputFormat%22:%20%22json%22%7D'

            try:
                handler  = urllib2.Request( url=url, data=text);
                handler = urllib2.urlopen(handler)
                response = handler.read().decode( 'utf-8' )
                response = json.loads( response.replace('\r\n', ''), strict=False )
                return response
            except:
                return None


    return None

    #if not ignoreSetneceLen :
    #if len( response['sentences'] ) > 1 and sentences == 'SINGLE' :
    #raise Exception( "Got multiple setneces for SINGLE" )
    #return None

    #if sentences == 'SINGLE' :
    #for key in response['sentences'][0].keys() :
    #response[key] = response['sentences'][0][key]

    #return response
