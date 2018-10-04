from flask import Flask, render_template, json, request, session, redirect, Response, stream_with_context, url_for
from flask_sse import sse
import time
from random import randint
import json, ast, serial

app = Flask(__name__)
app.secret_key = 'any random string'
ser = serial.Serial('/dev/ttyACM0',)


def getSignal(data):
    while True:
        shot = ser.readline()

        for dat in data["data"]:
            if dat["signal"] == shot:
                return dat["points"]
            
def get_shot():
    with open('dart.json') as f:
        temp = json.load(f)
    shot = int(getSignal(temp));
    if shot == 999:
        return 999
    else:
        return shot
    

def get_message(shotNumber, currentPlayer):
    with open('dart.json') as f:
        temp = json.load(f)
        
    data = session.get('data')
    numberPlayers =  len(data)   
    for x in range(0, numberPlayers):
        data[x]['current'] = 0
    
    data[currentPlayer]['current'] = 1
    
    shot = int(getSignal(temp));
    if shot == 999:
        return 999
    
    newPoints = int(data[currentPlayer]['points']) - shot    
    
    data[currentPlayer]['shot'] = shotNumber
    if newPoints == 0:
        print newPoints
        return redirect(url_for('winner'))
    elif newPoints > 0:
        data[currentPlayer]['points'] = str(newPoints)
        session['data'] = data
        return data
    else:
        return data

@app.route('/')
def main():
    session.clear()
    return render_template('index.html')


@app.route('/signUp',methods=['POST','GET'])
def signUp():
    try:
        players = request.form['inputPlayers']
        session['players'] = str(players)
        points = request.form['inputPoints']
        session['points'] = str(points)
        return json.dumps({'html':'<span>All fields good !!</span>'})
        

    except Exception as e:
        return json.dumps({'error':str(e)})
    
@app.route('/pregame')
def preGame():
    players = int(session['players'])
    points = session['points']
    return render_template('pregame.html', players=players, points=points)

@app.route('/game')
def game():
    players = session.get('players')
    
    data = []
    
    for x in range(0, int(players)):
        data.append({'points': session.get('points'), 'shot': 0, 'current': 0})
    
    data[0]['shot'] = 1
    data[0]['current'] = 1
    session['data'] = data
    print data
    return render_template('game.html')


@app.route('/winner')
def winner():
    winner = request.args.get('winner')
    return render_template('winner.html', winner=winner)


    
@app.route('/stream')
def stream():
    def eventStream():
        while True:
            temp = get_shot()
            if temp == 999:
                yield 'data: %s\n%s\n\n' % (json.dumps(session['data']),json.dumps("Start"))
                break
            
        while True:
            players = session.get('players')
            for y in range(0, int(players)):
                i = 2
                for x in range(0, 4):
                    # wait for source data to be available, then push it
                    
                    breaker = False
                    data = session.get('data')
                    temp = get_shot()
                    print temp
                    
                    if x == 3:
                        while True:
                            temp = get_shot()
                            if temp == 999:
                                print temp
                                data[y]['current'] = 0
                                data[(y+1)%(int(players))]['current'] = 1
                                data[y]['shot'] = 0
                                data[(y+1)%(int(players))]['shot'] = 1
                                breaker = True
                                
                                yield 'data: %s\n%s\n\n' % (json.dumps(data),json.dumps("Start"))
                            break
                    
                    if breaker:
                        break
                    
                    for z in range(0, int(players)):
                        data[z]['current'] = 0
                    data[y]['current'] = 1
                    data[y]['shot'] = str(i)
                    i = i + 1
                    if temp != 999:
                        newPoints = int(data[y]['points']) - temp
                        
                        
                        if newPoints == 0:
                            yield 'data: %s%s\n\n' % (json.dumps("Redirect"), json.dumps(y))
                        elif newPoints > 0:
                            data[y]['points'] = str(newPoints)
                            session['data'] = data
                            yield 'data: %s\n\n' % (json.dumps(data))
                        
                        else:
                            #TODO
                            yield 'data: %s\n\n' % (json.dumps(data))
                            
                    else:
                        data[y]['current'] = 0
                        data[(y+1)%(int(players))]['current'] = 1
                        data[y]['shot'] = 0
                        data[(y+1)%(int(players))]['shot'] = 1
                        session['data'] = data
                        yield 'data: %s\n%s\n\n' % (json.dumps(data),json.dumps("Continue"))
                        break
                                        
    return Response(stream_with_context (eventStream()), mimetype="text/event-stream")                        

if __name__ == "__main__":
    app.run(port=5000)
