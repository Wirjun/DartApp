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
            temp = get_message(0,0)
            if temp == 999:
                yield 'data: %s\n%s\n\n' % (json.dumps(session['data']),json.dumps("Start"))
                break
            
        while True:
            players = session.get('players')
            for y in range(0, int(players)):
                for x in range(0, 2):
                    # wait for source data to be available, then push it
                    session['shot'] = x
                    session['player'] = y 
                    try:
                        data = get_message(x,y)
                        
                        if data == 999:
                            yield 'data: %s\n%s\n\n' % (json.dumps(session['data']),json.dumps("Continue"))
                            break
                        else:
                            yield 'data: %s\n\n' % (json.dumps(get_message(x, y)))
                    
                    except TypeError as e:
                        yield 'data: %s%s\n\n' % (json.dumps("Redirect"), json.dumps(y))
                        
                    
                                        
    return Response(stream_with_context (eventStream()), mimetype="text/event-stream")                        

if __name__ == "__main__":
    app.run(port=5000)
