from flask import Flask, render_template, json, request, session, redirect, Response, stream_with_context, url_for
from flask_sse import sse
import time
from random import randint

app = Flask(__name__)
app.secret_key = 'any random string'

def get_message():    
    shot = randint(0, 9)    
    playersPoints = session.get('playersPoints')
    #print playersPoints
    player =  int(session.get('player'))
    
    #print player
    newPoints = int(playersPoints[player]) - shot
    #print newPoints
    time.sleep(2.0)
    if newPoints == 0:
        return redirect(url_for('winner'))
    elif newPoints > 0:
        playersPoints[player] = str(newPoints)
        session['playersPoints'] = playersPoints
        return newPoints
    else:
        return playersPoints[player]

@app.route('/')
def main():
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
    players = session.get('players')
    points = session.get('points')
    return render_template('pregame.html', players=players, points=points)

@app.route('/game')
def game():
    players = session.get('players')
    
    player = []
    for x in range(0, int(players)):
        player.append(session.get('points'))
    session['playersPoints'] = player    
    return render_template('game.html')

@app.route('/winner')
def winner():
    return render_template('winner.html')

    
@app.route('/stream')
def stream():
    def eventStream():
        while True:
            players = session.get('players')
            for y in range(0, int(players)):
                for x in range(0, 2):
                    # wait for source data to be available, then push it
                    session['shot'] = x
                    session['player'] = y
                    yield 'data: %s\ndata: %d \ndata: %d\n\n' % (format(get_message()), x+1, y+1)
                                        
    return Response(stream_with_context (eventStream()), mimetype="text/event-stream")                        

if __name__ == "__main__":
    app.run(port=5002)
